"""
Various functinos for traffic class generation
"""
from panacea.lps.topology.traffic import TrafficClass


def getClassesRegular(resources=None):
    """

    :param resources:
    :return:
    """
    classes = [TrafficClass('regular', 1.0, 10)]
    if resources is not None:
        for cl in classes:
            for r in resources:
                cl['{}cost'.format(r.lower())] = 1
    return classes


def getClassesEqual(classNames, resources=None):
    """

    :param classNames:
    :param resources:
    :return:
    """
    classes = []
    for cname in classNames:
        cl = TrafficClass(cname, 1.0 / len(classNames), 10)
        if resources is not None:
            for r in resources:
                cl[r.lower() + 'cost'] = 1

        classes.append(cl)
    return classes


def getClassesFromDict(d):
    """

    :param d:
    :return:
    """
    # Sanity check
    assert (sum(d.values()) == 1)
    classes = []
    for clname, (fraction, vol) in d.iteritems():
        classes.append(TrafficClass(clname, fraction, vol))
    return classes