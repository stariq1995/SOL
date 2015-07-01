package edu.unc.sol.app;

import org.json.simple.parser.ParseException;
import org.onlab.packet.MacAddress;
import org.onosproject.net.DeviceId;
import org.onosproject.net.HostId;
import org.onosproject.net.Link;
import org.onosproject.net.Path;
import org.onosproject.net.intent.ConnectivityIntent;
import org.onosproject.net.topology.impl.PathManager;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

//import org.onosproject.net.link.LinkStore;
//import org.onosproject.net.topology.PathService;

public class SolToOnos {
    protected PathManager pathManager;
    protected ParseSol parseSol;
    protected List<TrafficClass> trafficClassList;

    public void runSolOptimization() {
        try {
            trafficClassList = parseSol.getTrafficClassesFromSol();
        } catch (ParseException | IOException e) {
            System.err.println("Exception occured!!");
            return;
        }
    }

    public DeviceId toDeviceId(long devno) {
        return DeviceId.deviceId(String.format("of:00000000000000%02X", devno));
    }

    public HostId toHostId(long hostno) {
        int i;
        byte[] b = new byte[6];
        for (i = 0; i < 5; i++)
            b[i] = 0;
        b[i] = (byte) hostno;
        MacAddress mac = new MacAddress(b);
        return HostId.hostId(mac);
    }

    public int toDevno(DeviceId devid) {
        String dev = devid.toString();
        int len = dev.length();
        int Devno = Integer.parseInt(dev.substring(len - 3), 16);
        return Devno;
    }

    public ArrayList<DeviceId> getDeviceListPerTrafficClass(TrafficClass trafficClass) {
        ArrayList<DeviceId> devlist = new ArrayList<DeviceId>();
        int i;
        for (i = 0; i < trafficClass.pathlen; i++) {
            DeviceId dev = toDeviceId(trafficClass.nodes_on_path[i]);
            devlist.add(dev);
        }
        return devlist;
    }

    public Path getPathSol(ConnectivityIntent intent, DeviceId one, DeviceId two) {

        Set<Path> paths = pathManager.getPaths(one, two);
        Iterator<Path> path_iter = paths.iterator();
        Iterator<TrafficClass> tc_iter = trafficClassList.iterator();
        TrafficClass trafficClass = new TrafficClass();
        long devno1, devno2;
        ArrayList<DeviceId> devlist;
        devno1 = toDevno(one);
        devno2 = toDevno(two);
        while (tc_iter.hasNext()) {
            trafficClass = tc_iter.next();
            if (devno1 == trafficClass.src && devno2 == trafficClass.dst)
                break;
        }
        devlist = getDeviceListPerTrafficClass(trafficClass);
        while (path_iter.hasNext()) {
            List<Link> linklist;
            Path path = path_iter.next();
            linklist = path.links();
            if (isSolPathLink(linklist, devlist))
                return path;
        }
        //Path not found
        return null;
    }

    public boolean isSolPathLink(List<Link> linklist, ArrayList<DeviceId> devlist) {
        Iterator<Link> link_iter = linklist.iterator();
        Iterator<DeviceId> dev_iter = devlist.iterator();
        DeviceId dev1 = null, dev2 = null;
        if (dev_iter.hasNext())
            dev1 = dev_iter.next();
        if (dev_iter.hasNext())
            dev2 = dev_iter.next();
        if (dev1 == null || dev2 == null)
            return false;
        while (link_iter.hasNext() && dev2 != null) {
            Link link = link_iter.next();
            if (!(link.src().deviceId().equals(dev1)) ||
                    !(link.dst().deviceId().equals(dev2)))
                return false;
            dev1 = dev2;
            if (dev_iter.hasNext())
                dev2 = dev_iter.next();
            else
                dev2 = null;
        }
        if (link_iter.hasNext() == false && dev2 == null)
            return true;
        else
            return false;
    }

	/*
    public static void main(String args[])
	{
		SolToOnos s=new SolToOnos();
		for(int i=1;i<=20;i++)
		{
			System.out.println(s.mapHost(i).toString());
		}
		
	}*/
}
