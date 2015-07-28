package edu.unc.sol.app;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.type.TypeFactory;
import org.apache.felix.scr.annotations.*;
import org.onlab.packet.IpPrefix;
import org.onlab.rest.BaseResource;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.*;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.TrafficSelector;
import org.onosproject.net.intent.IntentService;
import org.onosproject.net.intent.PathIntent;
import org.onosproject.net.link.LinkService;
import org.onosproject.net.provider.ProviderId;
import org.slf4j.Logger;

import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

import static org.slf4j.LoggerFactory.getLogger;

@Component(immediate = true)
@javax.ws.rs.Path("/")
public class SolApp extends BaseResource {

    private final static Logger log = getLogger(SolApp.class.getSimpleName());
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected CoreService coreService;
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected IntentService intentService;
    PathIntent.Builder pathBuilder = PathIntent.builder();
    TrafficSelector.Builder selectorBuilder = DefaultTrafficSelector.builder();
    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    LinkService linkService;
    private ApplicationId appId;

    @Activate
    public void activate() {
        String myname = "edu.unc.sol";
        appId = coreService.registerApplication(myname);
        log.info("Activating SOL");
    }

    @Deactivate
    public void deactivate() {
        log.info("Deactivating. Intents will remain");
    }

    public boolean submitPath(SolPath p) {

        TrafficSelector s = selectorBuilder.matchIPSrc(IpPrefix.valueOf(p.srcprefix))
                .matchIPDst(IpPrefix.valueOf(p.dstprefix))
                .build();
        //TODO: more parameters for port matching
        PathIntent pi = pathBuilder.appId(appId)
                .selector(s)
                .path(convertPath(p))
                .build();
        intentService.submit(pi);
        return true;
    }

    protected Path convertPath(SolPath p) {
        ArrayList<Link> links = new ArrayList<>();
        for (int i = 0; i < p.nodes.length - 1; i++) {
            links.add(linkService.getLink(ConnectPoint.deviceConnectPoint(p.nodes[i]),
                    ConnectPoint.deviceConnectPoint(p.nodes[i + 1])));
        }
        return new DefaultPath(ProviderId.NONE, links, links.size());
    }

    @GET
    @javax.ws.rs.Path("hi")
    public Response helloWorld() {
        return Response.ok("Hi, I am SOL app").build();
    }

    @POST
    @javax.ws.rs.Path("install")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response installSOLPaths(InputStream input) {
        ObjectMapper mapper = new ObjectMapper();
        try {
            SolPath[] paths = mapper.readValue(input, SolPath[].class);
            boolean success = true;
            for (SolPath p : paths) {
                log.info(p.toString());
                success = submitPath(p);
                if (!success) {
                    break;
                }
            }
            if (success) {
                return Response.ok().build();
            } else {
                return Response.serverError().build();
            }
        } catch (IOException e) {
            log.error(e.getMessage());
        }
        return Response.ok("ok").build();

    }


//    public DeviceId toDeviceId(string devno) {
//        return DeviceId.deviceId(String.format("of:00000000000000%02X", Integer.parseInt(devno)));
//    }
//
//    public HostId toHostId(long hostno) {
//        int i;
//        byte[] b = new byte[6];
//        for (i = 0; i < 5; i++)
//            b[i] = 0;
//        b[i] = (byte) hostno;
//        MacAddress mac = new MacAddress(b);
//        return HostId.hostId(mac);
//    }
//
//    public int toDevno(DeviceId devid) {
//        String dev = devid.toString();
//        int len = dev.length();
//        int Devno = Integer.parseInt(dev.substring(len - 3), 16);
//        return Devno;
//    }
//
//    public ArrayList<DeviceId> getDeviceListPerTrafficClass(TrafficClass trafficClass) {
//        ArrayList<DeviceId> devlist = new ArrayList<DeviceId>();
//        int i;
//        for (i = 0; i < trafficClass.pathlen; i++) {
//            DeviceId dev = toDeviceId(trafficClass.nodes_on_path[i]);
//            devlist.add(dev);
//        }
//        return devlist;
//    }

//    public org.onosproject.net.Path getPathSol(ConnectivityIntent intent, DeviceId one, DeviceId two) {
//
//        Set<org.onosproject.net.Path> paths = pathManager.getPaths(one, two);
//        Iterator<org.onosproject.net.Path> path_iter = paths.iterator();
//        Iterator<TrafficClass> tc_iter = trafficClassList.iterator();
//        TrafficClass trafficClass = new TrafficClass();
//        long devno1, devno2;
//        ArrayList<DeviceId> devlist;
//        devno1 = toDevno(one);
//        devno2 = toDevno(two);
//        while (tc_iter.hasNext()) {
//            trafficClass = tc_iter.next();
//            if (devno1 == trafficClass.src && devno2 == trafficClass.dst)
//                break;
//        }
//        devlist = getDeviceListPerTrafficClass(trafficClass);
//        while (path_iter.hasNext()) {
//            List<Link> linklist;
//            org.onosproject.net.Path path = path_iter.next();
//            linklist = path.links();
//            if (isSolPathLink(linklist, devlist))
//                return path;
//        }
//        //SolPath not found
//        return null;
//    }
//
//    public boolean isSolPathLink(List<Link> linklist, ArrayList<DeviceId> devlist) {
//        Iterator<Link> link_iter = linklist.iterator();
//        Iterator<DeviceId> dev_iter = devlist.iterator();
//        DeviceId dev1 = null, dev2 = null;
//        if (dev_iter.hasNext())
//            dev1 = dev_iter.next();
//        if (dev_iter.hasNext())
//            dev2 = dev_iter.next();
//        if (dev1 == null || dev2 == null)
//            return false;
//        while (link_iter.hasNext() && dev2 != null) {
//            Link link = link_iter.next();
//            if (!(link.src().deviceId().equals(dev1)) ||
//                    !(link.dst().deviceId().equals(dev2)))
//                return false;
//            dev1 = dev2;
//            if (dev_iter.hasNext())
//                dev2 = dev_iter.next();
//            else
//                dev2 = null;
//        }
//        if (link_iter.hasNext() == false && dev2 == null)
//            return true;
//        else
//            return false;
//    }
}