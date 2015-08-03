package org.cmu.solapp;


import org.apache.felix.dm.Component;
import org.opendaylight.controller.sal.core.ComponentActivatorAbstractBase;
import org.opendaylight.controller.sal.flowprogrammer.IFlowProgrammerService;
import org.opendaylight.controller.switchmanager.ISwitchManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Activator extends ComponentActivatorAbstractBase {
    private static final Logger log = LoggerFactory.getLogger(PacketHandler.class);

    public Object[] getImplementations() {
        log.trace("Getting Implementations :-");
        Object[] res = {PacketHandler.class};
        return res;
    }

    public void configureInstance(Component c, Object imp, String containerName) {
        log.trace("Configuring instance..");

        if (imp.equals(PacketHandler.class)) {

            c.setInterface(new String[]{PacketHandler.class.getName()}, null);
            c.add(createContainerServiceDependency(containerName)
                    .setService(IFlowProgrammerService.class)
                    .setCallbacks("setFlowProgrammerService", "unsetFlowProgrammerService")
                    .setRequired(true));

            c.add(createContainerServiceDependency(containerName)
                    .setService(ISwitchManager.class)
                    .setCallbacks("setSwitchManagerService", "unsetSwitchManagerService")
                    .setRequired(true));

        }
    }


}

