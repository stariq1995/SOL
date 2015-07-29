package org.cmu.solapp;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.LinkedList;
import java.util.List;
//import java.util.Set;
import java.util.HashMap;
import java.util.regex.Pattern;
import java.util.ArrayList;
import java.util.Scanner;
import java.util.Set;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.File;
import java.io.IOException;

import org.opendaylight.controller.sal.action.Action;
import org.opendaylight.controller.sal.action.Output;
//import org.opendaylight.controller.sal.action.
import org.opendaylight.controller.sal.utils.INodeFactory;
//import org.opendaylight.controller.sal.action.Output;
//import org.opendaylight.controller.sal.action.SetDlDst;
//import org.opendaylight.controller.sal.action.SetDlSrc;
import org.opendaylight.controller.sal.action.SetNwDst;
//import org.opendaylight.controller.sal.action.SetNwSrc;
//import org.opendaylight.controller.sal.core.ConstructionException;
import org.opendaylight.controller.sal.core.Node;
import org.opendaylight.controller.sal.core.NodeConnector;
import org.opendaylight.controller.sal.flowprogrammer.Flow;
import org.opendaylight.controller.sal.flowprogrammer.IFlowProgrammerService;
import org.opendaylight.controller.sal.match.Match;
import org.opendaylight.controller.sal.match.MatchType;
//import org.opendaylight.controller.sal.packet.Ethernet;
//import org.opendaylight.controller.sal.packet.IDataPacketService;
//import org.opendaylight.controller.sal.packet.IListenDataPacket;
//import org.opendaylight.controller.sal.packet.IPv4;
//import org.opendaylight.controller.sal.packet.Packet;
//import org.opendaylight.controller.sal.packet.PacketResult;
//import org.opendaylight.controller.sal.packet.RawPacket;
//import org.opendaylight.controller.sal.packet.TCP;
//import org.opendaylight.controller.sal.utils.EtherTypes;
import org.opendaylight.controller.sal.utils.Status;
import org.opendaylight.controller.switchmanager.ISwitchManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.codehaus.jettison.json.JSONObject;
import org.codehaus.jettison.json.JSONArray;
import org.codehaus.jettison.json.JSONException;

public class PacketHandler { //implements IListenDataPacket {
    
    private static final Logger log = LoggerFactory.getLogger(PacketHandler.class);
    long starttime;
	long endtime;
    ArrayList<Thread> tlist;
    
    //private IDataPacketService dataPacketService;
    private IFlowProgrammerService flowProgrammerService;
    private ISwitchManager switchManager;
   
    static private InetAddress convertMaskToInet(String addr)
    {
    	String[] parts = addr.split("/");
	    String ip = parts[0];
	    int prefix;
	    if (parts.length < 2) {
	        prefix = 0;
	    } else {
	        prefix = Integer.parseInt(parts[1]);
	    }
	    int mask = 0xffffffff << (32 - prefix);
	    //System.out.println("Prefix=" + prefix);
	    //System.out.println("Address=" + ip);

	    int value = mask;
	    byte[] bytes = new byte[]{ 
	            (byte)(value >>> 24), (byte)(value >> 16 & 0xff), (byte)(value >> 8 & 0xff), (byte)(value & 0xff) };
	    InetAddress netAddr;
	    try {
	    	netAddr = InetAddress.getByAddress(bytes);
	    }
	    catch(UnknownHostException e)
	    {
	    	System.out.println("Mask could not be converted to InetAddress");
	    	return null;
	    }
	    //System.out.println("Mask=" + netAddr.getHostAddress());
	    return netAddr;
	}
    
    static private InetAddress intToInetAddress(int i) {
        byte b[] = new byte[] { (byte) ((i>>24)&0xff), (byte) ((i>>16)&0xff), (byte) ((i>>8)&0xff), (byte) (i&0xff) };
        InetAddress addr;
        try {
            addr = InetAddress.getByAddress(b);
        } catch (UnknownHostException e) {
            return null;
        }
        return addr;
    }
    
    static private byte[] stringToByteMac(String mac)
    {
    	String[] parts = mac.split(Pattern.quote(":"));
    	byte[] bytemac = new byte[6];
    	for(int i=0;i<parts.length;i++)
    	{
    		Integer hex = Integer.parseInt(parts[i], 16);
    		bytemac[i] = hex.byteValue();
    	}
    	return bytemac;
    }
    private NodeConnector stringToNodeConnector(Node node,String portnum)
    { 
    	//System.out.println("node="+node.toString());
    	String node_str = node.toString();
    	String[] parts = node_str.split(Pattern.quote("|"));
    	//System.out.println("Parts = "+parts[0]+parts[1]+parts[2]);
    	String s = portnum+"@OF";
    	String nc_str = parts[0]+"|"+s+"|"+parts[1];
    	//System.out.println("String="+nc_str);
    	return NodeConnector.fromString(nc_str);
    }
    
    static private InetAddress stringToInetAddress(String i)
    {
    	InetAddress addr;
    	String[] parts = i.split(Pattern.quote("/"));
    	if(parts.length >= 2)
    		i = parts[0];
    	try {
    		addr = InetAddress.getByName(i);
    	}
    	catch (UnknownHostException e) {
    		return null;
    	}
    	return addr;
    }
    	
    /*public PacketHandler() {
        try {
            publicInetAddress = InetAddress.getByName(PUBLIC_IP);
        } catch (UnknownHostException e) {
            log.error(e.getMessage());
        }
        
        try {
            server1Address = InetAddress.getByName(SERVER1_IP);
        } catch (UnknownHostException e) {
            log.error(e.getMessage());
        }
        
        try {
            server2Address = InetAddress.getByName(SERVER2_IP);
        } catch (UnknownHostException e) {
            log.error(e.getMessage());
        }
    }*/
    
    /**
     * Sets a reference to the requested DataPacketService
     */
    /*void setDataPacketService(IDataPacketService s) {
        log.trace("Set DataPacketService.");

        dataPacketService = s;
    }*/

    /**
     * Unsets DataPacketService
     */
    /*void unsetDataPacketService(IDataPacketService s) {
        log.trace("Removed DataPacketService.");

        if (dataPacketService == s) {
            dataPacketService = null;
        }
    }*/
    
    /**
     * Sets a reference to the requested FlowProgrammerService
     */
    void setFlowProgrammerService(IFlowProgrammerService s) {
        log.trace("Set FlowProgrammerService.");

        flowProgrammerService = s;
    }

    /**
     * Unsets FlowProgrammerService
     */
    void unsetFlowProgrammerService(IFlowProgrammerService s) {
        log.trace("Removed FlowProgrammerService.");

        if (flowProgrammerService == s) {
            flowProgrammerService = null;
        }
    }

    /**
     * Sets a reference to the requested SwitchManagerService
     */
    void setSwitchManagerService(ISwitchManager s) {
        log.trace("Set SwitchManagerService.");

        switchManager = s;
    }

    /**
     * Unsets SwitchManagerService
     */
    void unsetSwitchManagerService(ISwitchManager s) {
        log.trace("Removed SwitchManagerService.");

        if (switchManager == s) {
            switchManager = null;
        }
    }
    void init() {
		log.trace("INIT called!");
	}

	void destroy() {
		log.trace("DESTROY called!");
	}

	void start() throws IOException, InterruptedException {
		log.trace("START called!");
		tlist = new ArrayList<Thread>();
		try {
			this.installFlows();
		}catch(JSONException e)
		{
			System.out.println("Caught JSON Exception!");
		}
	}

	void stop() {
		log.debug("STOP called!");
	}
    
	private void executeSolOptimization() throws IOException, InterruptedException
	{
		String path = "/home/dipayan/sol/examples";
		ProcessBuilder pb = new ProcessBuilder("python","SIMPLER.py");
		pb.directory(new File(path));
		pb.redirectError();
		Process sol = pb.start();
		sol.waitFor();
	}
    public ArrayList<FlowFromSol> getFlowsFromSol() throws IOException, InterruptedException
    {	
    	starttime = System.currentTimeMillis();
    	executeSolOptimization();
    	endtime = System.currentTimeMillis();
    	System.out.println("\n\n\nExecuting sol = "+(endtime-starttime)+" msecs!\n\n\n");
    	starttime = System.currentTimeMillis();
    	
    	File jsfile = new File("/home/dipayan/flows.json");
    	if(!(jsfile.exists())) {
    		System.out.println("JSON file could not be found!");
    		return null;
    	}
    	ArrayList<FlowFromSol> flowList = new ArrayList<FlowFromSol>();
		Scanner in;
		try {
			in = new Scanner(new FileReader("/home/dipayan/flows.json"));
		}
		catch(FileNotFoundException e) {
			System.out.println("File Not Found");
			return null;
		}
		String str="";
		while(in.hasNextLine())
		{
			str = str.concat(in.nextLine())+"\n";
		}
		in.close();
		jsfile.delete();
		try {
			JSONArray arr = new JSONArray(str);
			for(int i=0;i<arr.length();i++)
			{
				JSONObject obj = arr.getJSONObject(i);
				FlowFromSol f = new FlowFromSol();
				f.flowName = obj.getString("flowName"); 
		        f.outPort = obj.getString("outPort");
		        //f.cookie = obj.getString("cookie");
		        f.ethDst = obj.getString("ethDst");; 
		        f.etherType = obj.getString("etherType");; 
		        f.ethSrc = obj.getString("ethSrc"); 
		        f.nodeId = obj.getString("nodeId"); 
		        f.inPort = obj.getString("inPort"); 
		        f.installHw = obj.getString("installHw"); 
		        f.priority = obj.getString("priority"); 
		        f.flowId = obj.getString("flowId");; 
		        f.srcIpPrefix = obj.getString("srcIpPrefix"); 
		        //f.tableId = obj.getString("tableId"); 
		        f.dstIpPrefix = obj.getString("dstIpPrefix");
			    flowList.add(f);
			}
		}catch(JSONException e) {
			System.out.println("Caught JSON Exception!");
			return null;
		}
		/*
		for(Flow flow : flowList)
		{
			System.out.println(flow.srcIpPrefix);
		}
		*/
		return flowList;
    }
    public void installFlows() throws JSONException, IOException, InterruptedException
    {
    	//Set<Node> allswitches;
    	
    	//allswitches = switchManager.getNodes();
    	//Object[] nodeList = allswitches.toArray();
    	//final long starttime = System.currentTimeMillis();
    	//final long starttime = System.currentTimeMillis();
    	ArrayList<FlowFromSol> flowList = getFlowsFromSol();
    	
    	for(FlowFromSol f : flowList)
    	{
    		Node node = Node.fromString(f.nodeId);
    		InstallFlowThread  flowThread = new InstallFlowThread(node,f);
            flowThread.start();
    	}
    	for(Thread t : tlist)
    		t.join();
    	endtime = System.currentTimeMillis();
    	System.out.println("\n\n\nInstalled "+flowList.size()+" flows!");
    	System.out.println("\n\n\nRule install time = "+(endtime-starttime)+" msecs!\n\n\n");
    	//System.out.println("\n\n\nSOL Optimization done in "+(endtime-starttime)+" msecs!\n\n\n");
    	/*
    	for(int i=0;i<nodeList.length;i++)
    	{
    		System.out.println("Switch"+i+"="+nodeList[i]);
    		System.out.println("Nodeconnectors=");
    		
    		for(int j=1;j<=5;j++)
    			System.out.println(stringToNodeConnector((Node)nodeList[i],String.valueOf(j)));
//    	}/OF|5@OF|00:00:00:00:00:00:00:04 = nodeconnector for switch4
    	*/
    	
    	//for(int i=0;i<list_of_switches.length;i++)
    		//System.out.println("Switch"+i+"="+list_of_switches[i].toString());
    	/*Output is :-
    	 * Switch0=OF|00:00:00:00:00:00:00:05
			Switch1=OF|00:00:00:00:00:00:00:04
			Switch2=OF|00:00:00:00:00:00:00:03
			Switch3=OF|00:00:00:00:00:00:00:02
			Switch4=OF|00:00:00:00:00:00:00:01
    	 
    	for(int i=0;i<nodeList.length;i++)
    		this.installFlowInNode((Node)nodeList[i]);
    	*/	
    	/*Match match = new Match();
    	match.setField(MatchType.DL_TYPE, (short)0x0800);
    	match.setField(MatchType.NW_DST, stringToInetAddress("10.0.0.2"));
    	match.setField(MatchType.NW_SRC, stringToInetAddress("10.0.0.1"));
    	match.setField(MatchType.NW_PROTO, (byte) 6);
    	
    	List<Action> actions = new LinkedList<Action>();
      
        actions.add(new SetNwDst(stringToInetAddress("10.0.0.2")));
        Flow flow = new Flow(match, actions);
        
        Node node = Node.fromString("OF|00:00:00:00:00:00:00:01");
        System.out.println("node="+node.toString());
        Status status = flowProgrammerService.addFlow(node, flow);
        if (!status.isSuccess()) {
            log.error("Could not program flow: " + status.getDescription());
        }
        */
    }
    /*
    public void installFlowInNode(Node node, FlowFromSol f) throws JSONException
    {	
    	
    	Match match = new Match();
        match.setField(MatchType.DL_TYPE, Short.parseShort(f.etherType));
        match.setField(MatchType.DL_DST, stringToByteMac(f.ethDst));
        match.setField(MatchType.DL_SRC, stringToByteMac(f.ethSrc));
        match.setField(MatchType.IN_PORT, stringToNodeConnector(node,f.inPort));
        match.setField(MatchType.NW_SRC, stringToInetAddress(f.srcIpPrefix),convertMaskToInet(f.srcIpPrefix));
        match.setField(MatchType.NW_DST, stringToInetAddress(f.dstIpPrefix),convertMaskToInet(f.dstIpPrefix));
        	
        	//match.setField(MatchType.NW_DST, stringToInetAddress("10.0.0.2"));
        	//match.setField(MatchType.NW_SRC, stringToInetAddress("10.0.0.1"));
        	//match.setField(MatchType.NW_PROTO, (byte) 6);
        	
        List<Action> actions = new LinkedList<Action>();
        NodeConnector nodeConn = stringToNodeConnector(node, f.outPort);
        actions.add(new Output(nodeConn));
        //InstallFlowThread  flowThread = new InstallFlowThread(node,f,match,actions);
        //flowThread.start();
        
        Flow flow = new Flow(match, actions);
        flow.setId(Long.parseLong(f.flowId));
        flow.setPriority(Short.parseShort(f.priority));
            
            //Node node = Node.fromString("OF|00:00:00:00:00:00:00:01");
            //System.out.println("node="+node.toString());
        Status status = flowProgrammerService.addFlow(node, flow);
        if (!status.isSuccess()) {
            log.error("Could not program flow: " + status.getDescription());
                System.out.println("Could not program flow in node "+node.toString()+": " + status.getDescription());
        }
        //else
         //	System.out.println("Successfully installed flows in node "+node.toString());
    }*/
    public class FlowFromSol
    {
    	String flowName; 
        String outPort;
        //String cookie;
        String ethDst; 
        String etherType; 
        String ethSrc; 
        String nodeId; 
        String inPort; 
        String installHw; 
        String priority; 
        String flowId; 
        String srcIpPrefix; 
        //String tableId; 
        String dstIpPrefix;
    }
    
    public class InstallFlowThread implements Runnable
    {
    	private Thread t;
    	Node node;
    	FlowFromSol f;
    	//Match match;
    	//List<Action> actions;
    	public InstallFlowThread(Node node, FlowFromSol f)
    	{
    		this.node = node;
    		this.f = f;
    		//this.match = match;
    		//this.actions = actions;
    	}
    	public void run()
    	{
    		Match match = new Match();
            match.setField(MatchType.DL_TYPE, Short.parseShort(f.etherType));
            match.setField(MatchType.DL_DST, stringToByteMac(f.ethDst));
            match.setField(MatchType.DL_SRC, stringToByteMac(f.ethSrc));
            match.setField(MatchType.IN_PORT, stringToNodeConnector(node,f.inPort));
            match.setField(MatchType.NW_SRC, stringToInetAddress(f.srcIpPrefix),convertMaskToInet(f.srcIpPrefix));
            match.setField(MatchType.NW_DST, stringToInetAddress(f.dstIpPrefix),convertMaskToInet(f.dstIpPrefix));
          	
            List<Action> actions = new LinkedList<Action>();
            NodeConnector nodeConn = stringToNodeConnector(node, f.outPort);
            actions.add(new Output(nodeConn));
            
            
            Flow flow = new Flow(match, actions);
            flow.setId(Long.parseLong(f.flowId));
            flow.setPriority(Short.parseShort(f.priority));
                
            Status status = flowProgrammerService.addFlow(node, flow);
            if (!status.isSuccess()) {
                log.error("Could not program flow: " + status.getDescription());
                    System.out.println("Could not program flow in node "+node.toString()+": " + status.getDescription());
            }
    	}
    	
    	public void start()
    	{
    		if(t==null)
    		{
    			t = new Thread(this);
    			tlist.add(t);
    			t.start();
    		}
    	}
    	
    }
}
