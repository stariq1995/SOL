package org.onosproject.sol;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
public class ParseSol 
{
	public ArrayList<TrafficClass> getTrafficClassesFromSol() throws IOException, ParseException, FileNotFoundException
	{
		
		JSONParser parser = new JSONParser();
		Object obj1 = parser.parse(new FileReader("$ONOS_ROOT/apps/onos-app-sol/src/main/java/org/onosproject/sol/f1.json"));
		Object obj2 = parser.parse(new FileReader("$ONOS_ROOT/onos/apps/onos-app-sol/src/main/java/org/onosproject/sol/f2.json"));
		JSONArray arr1 = (JSONArray)obj1;
		JSONArray arr2 = (JSONArray)obj2;
		ArrayList<TrafficClass> tclist = new ArrayList<TrafficClass>(); 
		for (Object o : arr1)
		{
			JSONObject TC = (JSONObject)o;
			TrafficClass tc = new TrafficClass();
			tc.volBytes = (long)TC.get("volBytes");
			tc.src = (long)TC.get("src");
			tc.volFlows = (long)TC.get("volFlows");
			tc.srcAppPorts = (String)TC.get("srcAppPorts");
			tc.dst = (long)TC.get("dst");
			tc.cpuCost = (long)TC.get("cpuCost");
			tc.priority = (long)TC.get("priority");
			tc.dstAppPorts = (String)TC.get("dstAppPorts");
			tc.srcIPPrefix = (String)TC.get("srcIPPrefix");
			tc.dstIPPrefix = (String)TC.get("dstIPPrefix");
			tc.ID = (long)TC.get("ID");
			tc.name = (String)TC.get("name");
			tclist.add(tc);
		}
		int j=0;
		Iterator<TrafficClass> tcit1 = tclist.iterator(); 
		for(Object o : arr2) 
		{
			TrafficClass tc = tcit1.next();
			j=0;
			JSONObject path = (JSONObject)o;
			JSONArray nodes_on_path = (JSONArray)path.get("nodes");
			for(Object o2 : nodes_on_path)
			{
				tc.nodes_on_path[j++] = (long)o2;
			}
			tc.pathlen=j;
			tc.numFlows=(double)path.get("numFlows");
			JSONArray useMBoxes = (JSONArray)path.get("useMBoxes");
			j=0;
			for(Object o2 : useMBoxes)
			{
				tc.useMBoxes[j++] = (long)o2;
			}
			tc.mboxlen=j;
			tc.PathWithMbox = (boolean)path.get("PathWithMbox");
		}
		/* For displaying, uncomment this :-
		j=0;
		Iterator<TrafficClass> tcit2 = tclist.iterator(); 
		while(tcit2.hasNext())
		{
			TrafficClass tc = tcit2.next();
			System.out.println("\nTraffic Class "+tc.ID);
			System.out.println("Name = "+tc.name);
			System.out.println("Source ="+tc.src);
			System.out.println("Destination ="+tc.dst);
			System.out.print("Path Taken = ");
			for(j=0;j<tc.pathlen;j++)
				System.out.print(tc.nodes_on_path[j]+" -> ");
			System.out.println();
			System.out.print("MBoxes at = ");
			for(j=0;j<tc.mboxlen;j++)
				System.out.print(tc.useMBoxes[j]+" , ");
			System.out.println();
			System.out.println("Number of flows = "+tc.numFlows);
		}*/
		return tclist;
	}
}
