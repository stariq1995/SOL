package edu.unc.sol.app;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.onlab.rest.BaseResource;
import org.slf4j.Logger;

import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.io.IOException;
import java.io.InputStream;

import static org.slf4j.LoggerFactory.getLogger;

/**
 * Created by victor on 9/2/15.
 */
@Path("/")
public class SolRestResource extends BaseResource {
    private final static Logger log = getLogger(SolApp.class.getSimpleName());


    @GET
    @Path("hi")
    public Response helloWorld() {
        return Response.ok("Hi, I am SOL app").build();
    }

    @POST
    @Path("install")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response installSOLPaths(InputStream input) {
        long start = System.currentTimeMillis();
        ObjectMapper mapper = new ObjectMapper();
        try {
            JsonNode data = mapper.readTree(input).get("paths");
            SolPath[] paths = mapper.treeToValue(data, SolPath[].class);
            SolApp instance = SolApp.getInstance();
            if (instance == null) {
                log.error("No instance of SolApp available");
                return Response.serverError().build();
            }
            for (SolPath p : paths) {
                boolean success = instance.submitPath(p);
                if (!success) { // Something went wrong
                    return Response.serverError().entity("Failed when sumbitting path. See ONOS log for details.").build();
                }
            }
        } catch (IOException e) {
            log.error(e.getMessage());
            return Response.serverError().build();
        }
        log.info("Install took: " + (System.currentTimeMillis() - start));
        return Response.ok("ok").build();
    }

    @GET
    @Path("clear")
    public Response removeAllFlows() {
        SolApp.getInstance().removeAllIntents();
        return Response.ok("ok").build();
    }

//    @GET
//    @Path("time")
//    public Response time() {
//        return Response.ok(Long.toString(SolApp.getInstance().getTime())).build();
//    }

    @GET
    @Path("shortest")
    public Response installShortestPaths(){
        if (SolApp.getInstance().installShortestPaths()) {
            return Response.ok("ok").build();
        } else {
            return Response.serverError().build();
        }
    }

    @GET
    @Path("cleanup")
    public Response cleanupOldIntents() {
        SolApp.getInstance().cleanupOldIntents();
        return Response.ok("ok").build();
    }

    @GET
    @Path("buildlinks")
    public Response buildLinks() {
        SolApp.getInstance().buildLinkMappings();
        return Response.ok("ok").build();
    }
}
