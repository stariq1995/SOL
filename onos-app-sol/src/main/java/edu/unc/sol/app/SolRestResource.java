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
//            if (paths.length > 400) {
//                Arrays.asList(paths).parallelStream().forEach((p) -> {
//                    instance.submitPath(p);
//                });
//            } else {
            for (SolPath p : paths) {
                instance.submitPath(p);
            }
//            }
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

    @GET
    @Path("time")
    public Response time() {
        return Response.ok(Long.toString(SolApp.getInstance().getTime())).build();
    }
}
