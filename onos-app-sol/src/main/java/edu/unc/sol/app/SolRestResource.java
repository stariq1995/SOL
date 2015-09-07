package edu.unc.sol.app;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.onlab.rest.BaseResource;
import org.slf4j.Logger;

import javax.ws.rs.*;
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
        ObjectMapper mapper = new ObjectMapper();
        try {
            JsonNode data = mapper.readTree(input).get("paths");
            SolPath[] paths = mapper.treeToValue(data, SolPath[].class);
            boolean success = true;
            for (SolPath p : paths) {
                log.info(p.toString());
                SolApp instance = SolApp.getInstance();
                if (instance == null) {
                    return Response.serverError().build();
                }
                success = instance.submitPath(p);
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

    @GET
    @Path("clear")
    public Response removeAllFlows() {
        SolApp.getInstance().removeAllIntents();
        return Response.ok("ok").build();
    }
}
