#!/bin/env python
#
# Time-stamp: "2017-08-01 14:37:43 jlenain"
#
## SGE parameters (this should work at CCIN2P3):
#$ -N processAllSources
#$ -e /sps/hess/lpnhe/jlenain/fermi/log
#$ -o /sps/hess/lpnhe/jlenain/fermi/log
#$ -j yes
#$ -l ct=02:00:00
#$ -l mem_free=2048M
#$ -l fsize=2048M
#$ -l xrootd=0
#$ -l sps=1
#$ -l os=sl6
#$ -p 0
#$ -P P_hess -cwd


"""
Process all sources for automatic aperture photometry of interesting high energy sources, with parametric batch jobs.

@author Jean-Philippe Lenain <mailto:jlenain@in2p3.fr>
"""

import sys
import os
import datetime
from optparse import OptionParser


# Import custom module
try:
    from flaapluc import automaticLightCurve as alc
except ImportError:
    print "\033[91mERROR\033[0m Can't import automaticLightCurve"
    sys.exit(1)


def main(argv=None):
    """
    Main procedure
    """

    # options parser:
    helpmsg="""%prog [options] <optional list of sources>

Use '-h' to get the help message

"""

    parser = OptionParser(version="%prog v1.2",
                          usage=helpmsg)

    parser.add_option("-d", "--daily", action="store_true", dest="d", default=False,
                      help='use daily bins for the light curves (defaulted to weekly).')
    parser.add_option("-c", "--custom-threshold", action="store_true", dest="c", default=False,
                      help='use custom trigger thresholds provided in the master list of sources (defaulted to 1.e-6 ph cm^-2 s^-1).')
    parser.add_option("-l", "--long-term", action="store_true", dest="l", default=False,
                      help='generate a long term light curve, using the whole mission time (defaulted to False).')
    parser.add_option("-m", "--merge-long-term", action="store_true", dest="m", default=False,
                      help='merge the long-term month-by-month light curves together.')
    parser.add_option("-u","--update",action="store_true",dest="u",default=False,
                      help='update with new data for last month/year when used in conjunction of --merge-long-term. Otherwise, has no effect.')
    parser.add_option("-w", "--with-history", action="store_true", dest="history", default=False,
                      help='use the long-term history of a source to dynamically determine a flux trigger threshold, instead of using a fixed flux trigger threshold as done by default. This option makes use of the long-term data on a source, and assumes that these have been previously generated with the --merge-long-term option.')
    parser.add_option("--stop-month", default=None, dest="STOPMONTH", metavar="<STOPMONTH>",
                      help="in conjunction with --merge-long-term, defines the stop year/month (in the format YYYYMM) until which the long-term light curve is generated. '%default' by default.")
    parser.add_option("-n", "--no-mail", action="store_true", dest="n", default=False,
                      help='do not send alert mails')
    parser.add_option("-t", "--test", action="store_true", dest="t", default=False,
                      help='for test purposes. Do not send the alert mail to everybody if a source is above the trigger threshold, but only to test recipients (by default, mail alerts are sent to everybody, cf. the configuration files).')
    parser.add_option("--dry-run", action="store_true", dest="dryRun", default=False,
                      help='only simulate what the pipeline would do, without actually processing any Fermi/LAT event.')
    parser.add_option("--use-parallel", action="store_true", default=False, dest="parallel",
                      help="use the linux program 'parallel' to use multiple threads on a local server.")
    parser.add_option("--max-cpu", default=1, dest="MAXCPU", metavar="<MAXCPU>",
                      help="in conjunction with --use-parallel, defines the number of CPU to use. Using '%default' by default.")
    parser.add_option("-f", "--config-file", default='default.cfg', dest="CONFIGFILE", metavar="CONFIGFILE",
                      help="provide a configuration file. Using '%default' by default.")
    parser.add_option("-v", "--verbose", action="store_true", dest="v", default=False,
                      help='verbose output.')

    (opt, args) = parser.parse_args()

    CONFIGFILE=opt.CONFIGFILE

    global VERBOSE
    if opt.v:
        VERBOSE=True
    else:
        VERBOSE=False

    # If dry run
    if opt.dryRun:
        DRYRUN=True
    else:
        DRYRUN=False

    # If parallel
    if opt.parallel:
        PARALLEL=True
        if int(opt.MAXCPU) != 1:
            MAXCPU=int(opt.MAXCPU)
        else:
            # Force the script to process only one source at a time
            MAXCPU=1
    else:
        PARALLEL=False
        
    # If daily bins
    if opt.d:
        DAILY=True
    else:
        DAILY=False

    # If custom thresholds
    if opt.c:
        USECUSTOMTHRESHOLD=True
    else:
        USECUSTOMTHRESHOLD=False

    # If test mode
    if opt.t:
        TEST=True
    else:
        TEST=False

    # If no mail is sent
    if opt.n:
        MAIL=False
    else:
        MAIL=True

    if TEST and not MAIL:
        print "\033[91mFATAL You asked for both the --test and --no-mail options."
        print "      These are mutually exclusive options.\033[0m"
        sys.exit(1)

    # If long term
    if opt.l:
        LONGTERM=True
    else:
        LONGTERM=False
    
    if LONGTERM is True and DAILY is True:
        print "\033[91mFATAL You asked for both the --long-term and --daily options."
        print "      Since this is too CPU intensive, this combination was disabled.\033[0m"
        sys.exit(1)


    # If merge long term light curves
    if opt.m:
        MERGELONGTERM=True
        # If update long term light curves with brand new data
        if opt.u:
            UPDATE=True
        else:
            UPDATE=False
        if opt.STOPMONTH is not None:
            STOPMONTH=str(opt.STOPMONTH)
        else:
            STOPMONTH=None
    else:
        MERGELONGTERM=False
        UPDATE=False
        STOPMONTH = None

    # If dynamical flux trigger threshold based on source history
    if opt.history:
        WITHHISTORY=True
    else:
        WITHHISTORY=False


    if(len(args)!=0):
        file=args[0]
        print "\033[93mINFO\033[0m Overriding default list of source: using %s" % file
        auto=alc(file=file,customThreshold=USECUSTOMTHRESHOLD,daily=DAILY,longTerm=LONGTERM,mergelongterm=MERGELONGTERM,withhistory=WITHHISTORY,configfile=CONFIGFILE,stopmonth=STOPMONTH)
    else:
        auto=alc(customThreshold=USECUSTOMTHRESHOLD,daily=DAILY,longTerm=LONGTERM,mergelongterm=MERGELONGTERM,withhistory=WITHHISTORY,configfile=CONFIGFILE,stopmonth=STOPMONTH)

    src,ra,dec,z,fglName=auto.readSourceList()


    # Total number of sources to process
    nbSrc=len(src)

    print
    print "I will process %i sources." % nbSrc
    print
    

    # Use the shell command "parallel"
    if PARALLEL:
        options=[]
        
        # Set the options for automaticLightCurve
        autoOptions=[]
        autoOptions.append("--config-file="+CONFIGFILE)
        if USECUSTOMTHRESHOLD:
            autoOptions.append("-c")
        if DAILY:
            autoOptions.append("-d")
        if MAIL is False:
            autoOptions.append("-n")
        if TEST:
            autoOptions.append("-t")
        if LONGTERM:
            autoOptions.append("-l")
        if MERGELONGTERM:
            autoOptions.append("-m")
            if UPDATE:
                autoOptions.append("-u")
            if STOPMONTH is not None:
                autoOptions.append("--stop-month=%s" % STOPMONTH)
        if WITHHISTORY:
            autoOptions.append("--with-history")

        # Loop on sources
        for i in range(nbSrc):
            options.append('\"/bin/nice -n 10 ./automaticLightCurve.py '+' '.join(autoOptions)+' '+str(src[i])+'\"')
        cmd="parallel -j "+str(MAXCPU)+" ::: "+" ".join(options)
        # use --dry-run just to test the parallel command
        if not DRYRUN:
            os.system(cmd)
        else:
            print cmd

    else:
        # Or directly process everything sequentially, using only 1 CPU
        if MERGELONGTERM:
            LONGTERM=True
        
        # Loop on sources
        for i in range(nbSrc):
            print 'Starting process %i for source %s' % (i,src[i])

            if not DRYRUN:
                processSrc(mysrc=src[i],useThresh=USECUSTOMTHRESHOLD,daily=DAILY,mail=MAIL,longTerm=LONGTERM,test=TEST,mergelongterm=MERGELONGTERM,withhistory=WITHHISTORY,update=UPDATE,configfile=CONFIGFILE)
            else:
                print "processSrc(mysrc="+src[i]+",useThresh="+str(USECUSTOMTHRESHOLD)+",daily="+str(DAILY)+",mail="+str(MAIL)+",longTerm="+str(LONGTERM)+",test="+str(TEST)+",mergelongterm="+str(MERGELONGTERM)+",withhistory="+str(WITHHISTORY)+",update="+str(UPDATE)+",configfile="+str(CONFIGFILE)+")"
            print

    return True



if __name__ == '__main__':
    """
    Execute main()
    """

    main()
