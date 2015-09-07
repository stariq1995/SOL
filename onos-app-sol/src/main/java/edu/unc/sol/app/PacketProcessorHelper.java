package edu.unc.sol.app;

import org.onlab.packet.*;
import org.onosproject.net.Host;
import org.onosproject.net.HostId;
import org.onosproject.net.Path;
import org.onosproject.net.PortNumber;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.flow.TrafficSelector;
import org.onosproject.net.flowobjective.DefaultForwardingObjective;
import org.onosproject.net.flowobjective.FlowObjectiveService;
import org.onosproject.net.flowobjective.ForwardingObjective;
import org.onosproject.net.host.HostService;
import org.onosproject.net.packet.InboundPacket;
import org.onosproject.net.packet.PacketContext;
import org.onosproject.net.packet.PacketProcessor;
import org.onosproject.net.topology.TopologyService;
import org.slf4j.Logger;

import java.util.Set;

import static org.slf4j.LoggerFactory.getLogger;


public class PacketProcessorHelper implements PacketProcessor {

    private final static Logger log = getLogger(PacketProcessorHelper.class.getSimpleName());
    private static final int DEFAULT_TIMEOUT = 10;
    public static final int DEFAULT_PRIORITY = 100;

    HostService hostService;
    TopologyService topologyService;
    FlowObjectiveService flowObjectiveService;

    public PacketProcessorHelper(HostService hs, TopologyService ts, FlowObjectiveService fos) {
        hostService = hs;
        topologyService = ts;
        flowObjectiveService = fos;
    }

    @Override
    public void process(PacketContext context) {
        // Stop processing if the packet has been handled, since we
        // can't do any more to it.
        if (context.isHandled()) {
            return;
        }

        InboundPacket pkt = context.inPacket();
        Ethernet ethPkt = pkt.parsed();

        if (ethPkt == null) {
            return;
        }

        // Bail if this is deemed to be a control packet.
        if (isControlPacket(ethPkt)) {
            return;
        }

        short pktType = ethPkt.getEtherType();

        // If ARP broadcast, flood
        if (pktType==Ethernet.TYPE_ARP && ethPkt.getDestinationMAC().equals(MacAddress.BROADCAST)) {
            flood(context);
            return;
        }

        HostId id = HostId.hostId(ethPkt.getDestinationMAC());
        // Do not process link-local addresses in any way.
        if (id.mac().isLinkLocal()) {
            return;
        }

        // Do we know who this is for? If not, flood ARPs or bail on the rest.
        Host dst = hostService.getHost(id);
        if (pktType == Ethernet.TYPE_ARP) {
            if (dst == null) {
                flood(context);
                return;
            }

            // Are we on an edge switch that our destination is on? If so,
            // simply forward out to the destination and bail.
            if (pkt.receivedFrom().deviceId().equals(dst.location().deviceId())) {
                if (!context.inPacket().receivedFrom().port().equals(dst.location().port())) {
                    packetOut(context, dst.location().port());
                }
                return;
            }

            // Otherwise, get a set of paths that lead from here to the
            // destination edge switch.
            Set<Path> paths =
                    topologyService.getPaths(topologyService.currentTopology(),
                            pkt.receivedFrom().deviceId(),
                            dst.location().deviceId());
            if (paths.isEmpty()) {
                // If there are no paths, flood and bail.
                flood(context);
                return;
            }

            // Otherwise, pick a path that does not lead back to where we
            // came from; if no such path, flood and bail.
            Path path = pickForwardPath(paths, pkt.receivedFrom().port());
            if (path == null) {
                log.warn("Doh... don't know where to go... {} -> {} received on {}",
                        ethPkt.getSourceMAC(), ethPkt.getDestinationMAC(),
                        pkt.receivedFrom());
                flood(context);
                return;
            }

            // Otherwise forward and be done with it.
            packetOut(context, path.src().port());
        } else if (pktType == Ethernet.TYPE_IPV4) { // Handle last hop
            if (dst == null) {
                log.warn("Cannot send to last hop");
                return;
            }
            log.info(dst.toString());
            if (pkt.receivedFrom().deviceId().equals(dst.location().deviceId())) {
                if (!pkt.receivedFrom().port().equals(dst.location().port())) {
                    log.info("here");
                    flowObjectiveService.forward(pkt.receivedFrom().deviceId(), DefaultForwardingObjective.builder()
                                    .withSelector(DefaultTrafficSelector.builder()
                                            .matchEthType(Ethernet.TYPE_IPV4)
                                            .matchEthDst(ethPkt.getDestinationMAC())
                                            .build())
                                    .withTreatment(DefaultTrafficTreatment.builder().setOutput(dst.location().port()).build())
                                    .withPriority(DEFAULT_PRIORITY)
                                    .makeTemporary(DEFAULT_TIMEOUT*10)
                                    .fromApp(SolApp.getInstance().getID())
                                    .withFlag(ForwardingObjective.Flag.VERSATILE).add()
                    );
                    packetOut(context, dst.location().port());
                }
            }
        }
    }

    private boolean isControlPacket(Ethernet eth) {
        short type = eth.getEtherType();
        return type == Ethernet.TYPE_LLDP || type == Ethernet.TYPE_BSN;
    }

    private void flood(PacketContext context) {
        if (topologyService.isBroadcastPoint(topologyService.currentTopology(),
                context.inPacket().receivedFrom())) {
            packetOut(context, PortNumber.FLOOD);
        } else {
            context.block();
        }
    }

    // Sends a packet out the specified port.
    private void packetOut(PacketContext context, PortNumber portNumber) {
        context.treatmentBuilder().setOutput(portNumber);
        context.send();
    }

    // Selects a path from the given set that does not lead back to the
    // specified port.
    private Path pickForwardPath(Set<Path> paths, PortNumber notToPort) {
        for (Path path : paths) {
            if (!path.src().port().equals(notToPort)) {
                return path;
            }
        }
        return null;
    }
}
