package org.cmu.solapp;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.ArrayList;
import java.util.Scanner;
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
    	executeSolOptimization();
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
		        f.cookie = obj.getString("cookie");
		        f.ethDst = obj.getString("ethDst");; 
		        f.etherType = obj.getString("etherType");; 
		        f.ethSrc = obj.getString("ethSrc"); 
		        f.nodeId = obj.getString("nodeId"); 
		        f.inPort = obj.getString("inPort"); 
		        f.installHw = obj.getString("installHw"); 
		        f.priority = obj.getString("priority"); 
		        f.flowId = obj.getString("flowId");; 
		        f.srcIpPrefix = obj.getString("srcIpPrefix"); 
		        f.tableId = obj.getString("tableId"); 
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
    	final long starttime = System.currentTimeMillis();
    	ArrayList<FlowFromSol> flowList = getFlowsFromSol();
    	for(FlowFromSol f : flowList)
    	{
    		Node node = Node.fromString(f.nodeId);
    		installFlowInNode(node,f);	
    	}
    	final long endtime = System.currentTimeMillis();
    	System.out.println("\n\n\nSOL Optimization done in "+(endtime-starttime)+" msecs!\n\n\n");
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
    }
    public class FlowFromSol
    {
    	String flowName; 
        String outPort;
        String cookie;
        String ethDst; 
        String etherType; 
        String ethSrc; 
        String nodeId; 
        String inPort; 
        String installHw; 
        String priority; 
        String flowId; 
        String srcIpPrefix; 
        String tableId; 
        String dstIpPrefix;
    }
    /*
    @Override
    public PacketResult receiveDataPacket(RawPacket inPkt) {
        // The connector, the packet came from ("port")
        NodeConnector ingressConnector = inPkt.getIncomingNodeConnector();
        // The node that received the packet ("switch")
        Node node = ingressConnector.getNode();
        
        log.trace("Packet from " + node.getNodeIDString() + " " + ingressConnector.getNodeConnectorIDString());
        
        // Use DataPacketService to decode the packet.
        Packet pkt = dataPacketService.decodeDataPacket(inPkt);
        
        if (pkt instanceof Ethernet) {
            Ethernet ethFrame = (Ethernet) pkt;
            Object l3Pkt = ethFrame.getPayload();
            
            if (l3Pkt instanceof IPv4) {
                IPv4 ipv4Pkt = (IPv4) l3Pkt;
                InetAddress clientAddr = intToInetAddress(ipv4Pkt.getSourceAddress());
                InetAddress dstAddr = intToInetAddress(ipv4Pkt.getDestinationAddress());
                Object l4Datagram = ipv4Pkt.getPayload();
                
                if (l4Datagram instanceof TCP) {
                    TCP tcpDatagram = (TCP) l4Datagram;
                    int clientPort = tcpDatagram.getSourcePort();
                    int dstPort = tcpDatagram.getDestinationPort();
                    
                    if (publicInetAddress.equals(dstAddr) && dstPort == SERVICE_PORT) {
                        log.info("Received packet for load balanced service");
                        
                        // Select one of the two servers round robin.
                        
                        InetAddress serverInstanceAddr;
                        byte[] serverInstanceMAC;
                        NodeConnector egressConnector;
                        
                        // Synchronize in case there are two incoming requests at the same time.
                        synchronized (this) {
                            if (serverNumber == 0) {
                                log.info("Server 1 is serving the request");
                                serverInstanceAddr = server1Address;
                                serverInstanceMAC = SERVER1_MAC;
                                egressConnector = switchManager.getNodeConnector(node, SERVER1_CONNECTOR_NAME);
                                serverNumber = 1;
                            } else {
                                log.info("Server 2 is serving the request");
                                serverInstanceAddr = server2Address;
                                serverInstanceMAC = SERVER2_MAC;
                                egressConnector = switchManager.getNodeConnector(node, SERVER2_CONNECTOR_NAME);
                                serverNumber = 0;
                            }
                        }
                                  
                        // Create flow table entry for further incoming packets
                        
                        // Match incoming packets of this TCP connection 
                        // (4 tuple source IP, source port, destination IP, destination port)
                        Match match = new Match();
                        match.setField(MatchType.DL_TYPE, (short) 0x0800);  // IPv4 ethertype
                        match.setField(MatchType.NW_PROTO, (byte) 6);       // TCP protocol id
                        match.setField(MatchType.NW_SRC, clientAddr);
                        match.setField(MatchType.NW_DST, dstAddr);
                        match.setField(MatchType.TP_SRC, (short) clientPort);
                        match.setField(MatchType.TP_DST, (short) dstPort);
                        
                        // List of actions applied to the packet
                        List<Action> actions = new LinkedList<Action>();
                        
                        // Re-write destination IP to server instance IP
                        actions.add(new SetNwDst(serverInstanceAddr));
                        
                        // Re-write destination MAC to server instance MAC
                        actions.add(new SetDlDst(serverInstanceMAC));
                        
                        // Output packet on port to server instance
                        actions.add(new Output(egressConnector));
                        
                        // Create the flow
                        Flow flow = new Flow(match, actions);
                        
                        // Use FlowProgrammerService to program flow.
                        Status status = flowProgrammerService.addFlow(node, flow);
                        if (!status.isSuccess()) {
                            log.error("Could not program flow: " + status.getDescription());
                            return PacketResult.CONSUME;
                        }
                                               
                        // Create flow table entry for response packets from server to client
                        
                        // Match outgoing packets of this TCP connection 
                        match = new Match();
                        match.setField(MatchType.DL_TYPE, (short) 0x0800); 
                        match.setField(MatchType.NW_PROTO, (byte) 6);
                        match.setField(MatchType.NW_SRC, serverInstanceAddr);
                        match.setField(MatchType.NW_DST, clientAddr);
                        match.setField(MatchType.TP_SRC, (short) dstPort);
                        match.setField(MatchType.TP_DST, (short) clientPort);
                        
                        // Re-write the server instance IP address to the public IP address
                        actions = new LinkedList<Action>();
                        actions.add(new SetNwSrc(publicInetAddress));
                        actions.add(new SetDlSrc(SERVICE_MAC));
                        
                        // Output to client port from which packet was received
                        actions.add(new Output(ingressConnector));
                        
                        flow = new Flow(match, actions);
                        status = flowProgrammerService.addFlow(node, flow);
                        if (!status.isSuccess()) {
                            log.error("Could not program flow: " + status.getDescription());
                            return PacketResult.CONSUME;
                        }
                        
                        // Forward initial packet to selected server
                      
                        log.trace("Forwarding packet to " + serverInstanceAddr.toString() + " through port " + egressConnector.getNodeConnectorIDString());
                        ethFrame.setDestinationMACAddress(serverInstanceMAC);
                        ipv4Pkt.setDestinationAddress(serverInstanceAddr);
                        inPkt.setOutgoingNodeConnector(egressConnector);                       
                        dataPacketService.transmitDataPacket(inPkt);
                        
                        return PacketResult.CONSUME;
                    }
                }
            }
        }
        
        // We did not process the packet -> let someone else do the job.
        return PacketResult.IGNORED;
    }*/

}
