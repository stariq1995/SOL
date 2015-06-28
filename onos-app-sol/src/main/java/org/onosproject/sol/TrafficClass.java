package org.onosproject.sol;
import java.util.List;
public class TrafficClass 
{
	String srcAppPorts,dstAppPorts,srcIPPrefix,dstIPPrefix,name;
	long volBytes,src,volFlows,dst,cpuCost,priority,ID;
	long[] nodes_on_path=new long[20];
	int pathlen;
	double numFlows;
	long[] useMBoxes=new long[20];
	int mboxlen;
	boolean PathWithMbox;
}
