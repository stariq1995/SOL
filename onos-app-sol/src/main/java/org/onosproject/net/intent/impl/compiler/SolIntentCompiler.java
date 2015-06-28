package org.onosproject.net.intent.impl.compiler;

import org.apache.felix.scr.annotations.Activate;
import org.apache.felix.scr.annotations.Component;
import org.apache.felix.scr.annotations.Deactivate;
import org.onosproject.net.ConnectPoint;
//import org.onosproject.net.DefaultPath;
//import org.onosproject.net.Link;
import org.onosproject.net.Path;
import org.onosproject.net.intent.Intent;
import org.onosproject.net.intent.PathIntent;
import org.onosproject.net.intent.SolIntent;
//import org.onosproject.net.provider.ProviderId;
import org.onosproject.net.resource.link.LinkResourceAllocations;
import org.onosproject.net.intent.SolIntent;
import org.onosproject.sol.SolToOnos;

//import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import static java.util.Arrays.asList;
//import static org.onosproject.net.DefaultEdgeLink.createEdgeLink;

//import static org.onosproject.net.flow.DefaultTrafficSelector.builder;

/**
 * SolIntent Compiler
 */
@Component(immediate = true)
public class SolIntentCompiler 
		extends ConnectivityIntentCompiler<SolIntent> {
	//private static final ProviderId PID = new ProviderId("core", "org.onosproject.core", true);
	public static final int DEFAULT_COST = 1;
	protected SolToOnos S2O;
	
	@Activate
    public void activate() {
        intentManager.registerCompiler(SolIntent.class, this);
        S2O.runSolOptimization();
        System.out.println("SOL Optimization Intent Service has started!");
    }

    @Deactivate
    public void deactivate() {
        intentManager.unregisterCompiler(SolIntent.class);
        System.out.println("SOL Optimization Intent Service has stopped!");
    }
    public List<Intent> compile(SolIntent intent, List<Intent> installable,
            Set<LinkResourceAllocations> resources) {
    	
    	ConnectPoint ingressPoint = intent.ingressPoint();
        ConnectPoint egressPoint = intent.egressPoint();
  
        //List<Link> links = new ArrayList<>();
        Path path = S2O.getPathSol(intent, ingressPoint.deviceId(), egressPoint.deviceId());
        return asList(createPathIntent(path, intent));
    }
    private Intent createPathIntent(Path path, SolIntent intent) {
    	return PathIntent.builder()
                .appId(intent.appId())
                .selector(intent.selector())
                .treatment(intent.treatment())
                .path(path)
                .constraints(intent.constraints())
                .priority(intent.priority())
                .build();
    }
    
	
	
	
	
	
	
	
	
	
	
	
	
	
	
}