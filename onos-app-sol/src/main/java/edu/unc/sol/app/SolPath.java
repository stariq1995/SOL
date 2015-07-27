package edu.unc.sol.app;

import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import java.util.Arrays;

@XmlRootElement
class SolPath {
    @XmlElement(name = "nodes")
    public String[] nodes;
    @XmlElement(name = "srcprefix")
    public String srcprefix;
    @XmlElement(name = "dstprefix")
    public String dstprefix;
    @XmlElement(name = "srcport")
    public String srcport;
    @XmlElement(name = "dstport")
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