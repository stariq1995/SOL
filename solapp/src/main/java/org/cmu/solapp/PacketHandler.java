package org.cmu.solapp;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.regex.Pattern;
import java.util.ArrayList;
import java.util.Scanner;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.File;
import java.io.IOException;
import org.opendaylight.controller.sal.action.Action;
import org.opendaylight.controller.sal.action.Output;
import org.opendaylight.controller.sal.core.Node;
import org.opendaylight.controller.sal.core.NodeConnector;
import org.opendaylight.controller.sal.flowprogrammer.Flow;
import org.opendaylight.controller.sal.flowprogrammer.IFlowProgrammerService;
import org.opendaylight.controller.sal.match.Match;
import org.opendaylight.controller.sal.match.MatchType;
import org.opendaylight.controller.sal.utils.Status;
import org.opendaylight.controller.switchmanager.ISwitchManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.codehaus.jettison.json.JSONObject;
import org.codehaus.jettison.json.JSONArray;
import org.codehaus.jettison.json.JSONException;

public class PacketHandler { 
    
    private static final Logger log = LoggerFactory.getLogger(PacketHandler.class);
    private static final byte MAXTHREADS = 8;
    long starttime;
	long endtime;
    ArrayList<Thread> tlist;
    BlockingQueue<InstallFlowThread> flowThreadList;
    int countFlows;
    int numFlows;
    
    private IFlowProgrammerService flowProgrammerService;
    private ISwitchManager switchManager;
   
    static private InetAddress convertMaskToInet(String addr)
    {
    	String[] parts = addr.split("/");
	    //String ip = parts[0];
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
    	String node_str = node.toString();
    	String[] parts = node_str.split(Pattern.quote("|"));
    	
    	String s = portnum+"@OF";
    	String nc_str = parts[0]+"|"+s+"|"+parts[1];
    	
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
    	
    void setFlowProgrammerService(IFlowProgrammerService s) {
        log.trace("Set FlowProgrammerService.");

        flowProgrammerService = s;
    }

    void unsetFlowProgrammerService(IFlowProgrammerService s) {
        log.trace("Removed FlowProgrammerService.");

        if (flowProgrammerService == s) {
            flowProgrammerService = null;
        }
    }

    void setSwitchManagerService(ISwitchManager s) {
        log.trace("Set SwitchManagerService.");

        switchManager = s;
    }

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
		flowThreadList = new LinkedBlockingQueue<InstallFlowThread>();
		countFlows = 0;

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
    public JSONArray getFlowsFromSol() throws IOException, InterruptedException
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
		JSONArray arr;
		try {
			arr = new JSONArray(str);
		}catch(JSONException e)
		{
			e.printStackTrace();
			return null;
		}
		numFlows = arr.length();
		System.out.println("Number of flows got from SOL = "+numFlows);
		return arr;
    }
		
	public void processFlowsFromSol(JSONArray arr) throws InterruptedException
	{
		try {
		for(int i=0;i<numFlows;i++)
		{
			JSONObject obj = arr.getJSONObject(i);
			FlowFromSol f = new FlowFromSol();
			f.flowName = obj.getString("flowName"); 
		    f.outPort = obj.getString("outPort");
		    f.ethDst = obj.getString("ethDst");; 
		    f.etherType = obj.getString("etherType");; 
		    f.ethSrc = obj.getString("ethSrc"); 
		    f.nodeId = obj.getString("nodeId"); 
		    f.inPort = obj.getString("inPort"); 
		    f.installHw = obj.getString("installHw"); 
		    f.priority = obj.getString("priority"); 
		    f.flowId = obj.getString("flowId");; 
		    f.srcIpPrefix = obj.getString("srcIpPrefix");  
		    f.dstIpPrefix = obj.getString("dstIpPrefix");
			InstallFlowThread flowThread = new InstallFlowThread(f);
	    	flowThreadList.put(flowThread);
		}
		}catch(JSONException e) {
			System.out.println("Caught JSON Exception!");
			return;
		}
    }
	
    public void installFlows() throws JSONException, IOException, InterruptedException
    {
    	long startime_overall = System.currentTimeMillis();
    	JSONArray arr = getFlowsFromSol();
    	for(int i=1;i<=MAXTHREADS;i++)
    	{
    		Thread t = new Thread(new Worker("Thread"+String.valueOf(i)));
    		tlist.add(t);
    		t.start();
    	}
    	processFlowsFromSol(arr);
    	
    	for(Thread t : tlist)
    	{
    		t.join(10);
    		t.interrupt();
    	}
    	endtime = System.currentTimeMillis(); 
    	System.out.println("\n\n\nInstalled "+numFlows+" flows!");
    	System.out.println("\n\n\nRule install time = "+(endtime-starttime)+" msecs!\n\n\n");
    	System.out.println("\n\n\nOverall Time = "+(endtime-startime_overall)+" msecs!\n\n\n");
    }
    public class FlowFromSol
    {
    	String flowName; 
        String outPort;
        String ethDst; 
        String etherType; 
        String ethSrc; 
        String nodeId; 
        String inPort; 
        String installHw; 
        String priority; 
        String flowId; 
        String srcIpPrefix;  
        String dstIpPrefix;
    }
    
    public class InstallFlowThread 
    {
    	FlowFromSol f;	
    	public InstallFlowThread(FlowFromSol f)
    	{
    		this.f = f;
    	}
    	public void install()
    	{
    		Node node;
    		
    		node = Node.fromString(f.nodeId);
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
    }
    public class Worker implements Runnable
    {
    	String threadName;
    	public Worker(String tname)
    	{
    		threadName = tname;
    	}
    	public void run()
    	{
    		while(countFlows < numFlows)
    		{
    			InstallFlowThread t;
    			try
    			{
    				t = flowThreadList.take();
    				countFlows++;
    			}
    			catch(InterruptedException e)
    			{
    				e.printStackTrace();
    				return;
    			}
    			//System.out.println("Countflows="+countFlows+" numFlows="+numFlows);
    			t.install();
    		}
    		//System.out.println("Countflows ="+countFlows+" "+threadName+" is exitting!");
    	}
    }
}
