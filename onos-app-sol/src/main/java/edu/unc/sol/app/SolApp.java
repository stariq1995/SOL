package edu.unc.sol.app;

import org.apache.felix.scr.annotations.*;
import org.onlab.packet.Ethernet;
import org.onlab.packet.IpPrefix;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.DefaultPath;
import org.onosproject.net.DeviceId;
import org.onosproject.net.Link;
import org.onosproject.net.Path;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.*;
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
import java.util.List;

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
    private List<Intent> allIntents = new ArrayList<>();

    private static SolApp instance = null;
    private static long time = 0;

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

//        new Thread(new Runnable() {
//            @Override
//            public void run() {
//                while (true) {
//                    for (Intent i : intentService.getIntents()) {
//                        if (i.appId().equals(appId)) {
//                            if (intentService.getIntentState(i.key()) == IntentState.WITHDRAWN) {
//                                intentService.purge(i);
//                            }
//                        }
//                    }
//                    try {
//                        Thread.sleep(2000);
//                    } catch (InterruptedException e) {
//                        break;
//                    }
//                }
//            }
//        }).start();
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

    public void submitPath(SolPath p) {
        TrafficSelector s = DefaultTrafficSelector.builder()
                .matchEthType(Ethernet.TYPE_IPV4)
                .matchIPSrc(IpPrefix.valueOf(p.srcprefix))
                .matchIPDst(IpPrefix.valueOf(p.dstprefix))
                .build();
        //TODO: more parameters for port matching
        long start = System.currentTimeMillis();
        Path onosPath = convertPath(p);
        time += System.currentTimeMillis() - start;
        PathIntent pi = PathIntent.builder().appId(appId)
                .selector(s)
                .path(onosPath)
                .build();
        allIntents.add(pi);
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
    }

    protected Path convertPath(SolPath p) {
        ArrayList<Link> pathlinks = new ArrayList<>();
        for (int i = 0; i < p.nodes.length - 1; i++) {
            for (Link l : linkService.getDeviceEgressLinks(DeviceId.deviceId(p.nodes[i]))) {
                // Note: currently no support for multi-graphs
                if (l.dst().deviceId().equals(DeviceId.deviceId(p.nodes[i + 1]))) {
                    pathlinks.add(l);
                    break;
                }
            }
        }
        return new DefaultPath(ProviderId.NONE, pathlinks, pathlinks.size());
    }

    void removeAllIntents() {
        long start = System.currentTimeMillis();
        ArrayList<Intent> intentsCopy = new ArrayList<>(allIntents);
        for (Intent pi : intentsCopy) {
            intentService.withdraw(pi);
            allIntents.remove(pi);
        }
        flowService.removeFlowRulesById(appId);
        log.info("Clear took: " + since(start));
    }

    private long since(long t) {
        return System.currentTimeMillis() - t;
    }

    public ApplicationId getID() {
        return appId;
    }

    public long getTime() {
        long a = time;
        time=0;
        log.info("convert time: " + a);
        return a;

    }

}