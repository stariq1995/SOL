package edu.unc.sol.app;

import javax.ws.rs.WebApplicationException;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.MultivaluedMap;
import javax.ws.rs.ext.MessageBodyReader;
import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import java.io.IOException;
import java.io.InputStream;
import java.lang.annotation.Annotation;
import java.lang.reflect.Type;
import java.util.Arrays;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlRootElement
class SolPath {
//    @XmlElement(name = "nodes")
    public String[] nodes;
//    @XmlElement(name = "srcprefix")
    public String srcprefix;
//    @XmlElement(name = "dstprefix")
    public String dstprefix;
//    @XmlElement(name = "srcport")
    public String srcport;
//    @XmlElement(name = "dstport")
    public String dstport;

    @Override
    public String toString() {
        return "SolPath{" +
                "nodes=" + Arrays.toString(nodes) +
                ", srcprefix='" + srcprefix + '\'' +
                ", dstprefix='" + dstprefix + '\'' +
                ", srcport='" + srcport + '\'' +
                ", dstport='" + dstport + '\'' +
                '}';
    }
}
//
//public class SolPathMessageBodyReader implements MessageBodyReader<SolPath> {
//
//    @Override
//    public boolean isReadable(Class<?> type, Type genericType,
//                              Annotation[] annotations, MediaType mediaType) {
//        return type == SolPath.class;
//    }
//
//    @Override
//    public SolPath readFrom(Class<SolPath> type,
//                           Type genericType,
//                           Annotation[] annotations, MediaType mediaType,
//                           MultivaluedMap<String, String> httpHeaders,
//                           InputStream entityStream)
//            throws IOException, WebApplicationException {
//
//        try {
//            JAXBContext jaxbContext = JAXBContext.newInstance(MyBean.class);
//            SolPath p = (SolPath) jaxbContext.createUnmarshaller()
//                    .unmarshal(entityStream);
//            return p;
//        } catch (JAXBException jaxbException) {
//            throw new Exception("Error deserializing a path.");
//        }
//    }
//}