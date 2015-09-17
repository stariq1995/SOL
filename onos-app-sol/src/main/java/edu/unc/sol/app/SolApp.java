package edu.unc.sol.app;

import org.apache.felix.scr.annotations.*;
import org.onlab.packet.Ethernet;
import org.onlab.packet.IpPrefix;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.*;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.net.flow.TrafficSelector;
import org.onosproject.net.flowobjective.DefaultForwardingObjective;
import org.onosproject.net.flowobjective.FlowObjectiveService;
import org.onosproject.net.flowobjective.ForwardingObjective;
import org.onosproject.net.host.HostService;
import org.onosproject.net.intent.Intent;
import org.onosproject.net.intent.IntentService;
import org.onosproject.net.intent.IntentState;
import org.onosproject.net.intent.PathIntent;
import org.onosproject.net.link.LinkService;
import org.onosproject.net.packet.PacketPriority;
import org.onosproject.net.packet.PacketService;
import org.onosproject.net.provider.ProviderId;
import org.onosproject.net.topology.TopologyService;
import org.slf4j.Logger;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

import static org.slf4j.LoggerFactory.getLogger;

@Component(immediate = true)
public class SolApp {

    private final static Logger log = getLogger(SolApp.class.getSimpleName());

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected CoreService coreService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected IntentService intentService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected LinkService linkService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected DeviceService deviceService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowObjectiveService foService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowRuleService flowService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected PacketService packetService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected TopologyService topologyService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected HostService hostService;

    private ApplicationId appId;

    private static SolApp instance = null;

    private class StringLink {
        private String src;
        private String dst;

        public StringLink(String src, String dst) {
            this.src = src;
            this.dst = dst;
        }

        public String getSrc() {
            return src;
        }

        public String getDst() {
            return dst;
        }

    }

    private Map<StringLink, Link> nodesToLinks;

    @Activate
    public void activate() {
        appId = coreService.registerApplication("edu.unc.sol");
        packetService.addProcessor(new PacketProcessorHelper(hostService, topologyService, foService),
                PacketProcessorHelper.ADVISOR_MAX + 2);
        TrafficSelector.Builder selector = DefaultTrafficSelector.builder();
        selector.matchEthType(Ethernet.TYPE_IPV4);
        packetService.requestPackets(selector.build(), PacketPriority.REACTIVE, appId);
        selector.matchEthType(Ethernet.TYPE_ARP);
        packetService.requestPackets(selector.build(), PacketPriority.REACTIVE, appId);

        instance = this;

        // Precompute link mappings:
        buildLinkMappings();

        log.info("Activated SOL");
    }

    @Deactivate
    public void deactivate() {
        log.info("Deactivating SOL");
        removeAllIntents();
        instance = null;
    }

    public static SolApp getInstance() {
        return instance;
    }

    public boolean submitPath(SolPath p) {
        TrafficSelector s = DefaultTrafficSelector.builder()
                .matchEthType(Ethernet.TYPE_IPV4)
                .matchIPSrc(IpPrefix.valueOf(p.srcprefix))
                .matchIPDst(IpPrefix.valueOf(p.dstprefix))
                .build();
        //TODO: more parameters for port matching
        Path onosPath = null;
        try {
            onosPath = convertPath(p);
        } catch (NoSuchLinkException e) {
            log.error("Could not convert SOL path to ONOS path. Please try re-building the link mapping");
            return false;
        }
        PathIntent pi = PathIntent.builder().appId(appId)
                .selector(s)
                .path(onosPath)
                .build();
        intentService.submit(pi);

        // Add the edge link treatment
        // Ingress
        foService.forward(onosPath.src().deviceId(), DefaultForwardingObjective.builder()
                .withSelector(s)
                .withTreatment(DefaultTrafficTreatment.builder().setOutput(onosPath.src().port()).build())
                .withPriority(PacketProcessorHelper.DEFAULT_PRIORITY)
                .fromApp(appId)
                .makePermanent()
                .withFlag(ForwardingObjective.Flag.VERSATILE).add());

        // Egress will get handled by the packet processor helper

        // Return ok
        return true;
    }

    protected Path convertPath(SolPath p) throws NoSuchLinkException {
        ArrayList<Link> pathlinks = new ArrayList<>(p.nodes.length);
        for (int i = 0; i < p.nodes.length - 1; i++) {
            Link l = nodesToLinks.get(new StringLink(p.nodes[i], p.nodes[i + 1]));
            if (l == null) {
                throw new NoSuchLinkException();
            }
            pathlinks.add(l);
        }
        return new DefaultPath(ProviderId.NONE, pathlinks, pathlinks.size());
    }

    void removeAllIntents() {
        for (Intent i : intentService.getIntents()) {
            if (i.appId().equals(appId)) {
                intentService.withdraw(i);
            }
        }
        flowService.removeFlowRulesById(appId);
    }

    void cleanupOldIntents() {
        for (Intent i : intentService.getIntents()) {
            if (i.appId().equals(appId) && intentService.getIntentState(i.key()) == IntentState.WITHDRAWN) {
                intentService.purge(i);
            }
        }
    }

    void installShortestPaths() {
        Iterable<Device> devices = deviceService.getDevices();
        for (Device d1 : devices) {
            for (Device d2 : devices) {
                if (d1.equals(d2)) continue;
                Collection<Path> paths = topologyService.getPaths(topologyService.currentTopology(), d1.id(), d2.id());
                if (paths.isEmpty()) {
                    log.error("No path between " + d1.toString() + " and " + d2.toString());
                    return;
                }
//                log.info(paths.toString());
                Path p = (Path) paths.toArray()[0];
//                log.info(p.toString());
                intentService.submit(PathIntent.builder()
                        .appId(appId)
                        .path(p)
                        .priority(100)
                        .selector(DefaultTrafficSelector.builder().matchEthType(Ethernet.TYPE_IPV4).build())
                        .build());
            }
        }
    }

    public ApplicationId getID() {
        return appId;
    }

    public void buildLinkMappings() {
        nodesToLinks = new HashMap<>(topologyService.currentTopology().linkCount());
        for (Device d : deviceService.getDevices()) {
            DeviceId src = d.id();
            String strid = src.toString();
            for (Link l : linkService.getDeviceEgressLinks(src)) {
                // Note: currently no support for multi-graphs
                nodesToLinks.put(new StringLink(strid, l.dst().deviceId().toString()), l);
            }
        }
    }

}