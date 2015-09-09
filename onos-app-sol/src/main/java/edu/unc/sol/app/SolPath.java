package edu.unc.sol.app;

import java.util.Arrays;

class SolPath {
    public String[] nodes;
    public String srcprefix;
    public String dstprefix;
    public String srcport;
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