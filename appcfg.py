''' appcfg.py .. central application configuration module
    it is used in the app, as well as in the python moduls in libxkm
'''
__version__ = "1.0"

import os
import configparser
from pathlib import Path
from dataclasses import dataclass, field


import appdef
import meassys
CFG_APPDIR = os.path.abspath("../")

#enable/disable additional debugging functionality
DBG_OUT = True

#important for attribute parsing and actions
DEF_IDENTIFIER_FILE = "p_file_"
DEF_IDENTIFIER_DIR = "p_dir_"

DEF_INISEC_USERFIELDS = "userfields" #settings the last user can override, if needed
DEF_INISEC_GENERAL = "general" 
DEF_INISEC_VERSION = "version"
DEF_INISEC_GUI = "gui-settings"


@dataclass
class ConfigApp():
    '''
    general Application Configuration class for XKM -> focus is on the configuration of application logic, path and folder definitions
    and so on 
    '''
    ##############################
    # internal working variables #
    ##############################
    appmode = ""  #sets the software operation mode 
    appname = "PRIMA"#the short application name
    apptitle = "PRIMA"  #the longer application title default application title    
    
    lang = "DE" #appdef.DEF_LANG_DE #configure the starting language (is also the default)
    version_app = "1.0"  #application versoin
    version_svn = "2237" #svn version
    version_appcfg = __version__ #module version i.e., for INI files
    builddate = "26.07.2023" #build date
    
    max_logfile_size = 1 # maximale Dateigröße der Log-Datei in MB
    
    
    ###########################################
    # application configuration (in ini file) #
    ###########################################
    app_loginmode = 1
    
    ####################################
    # measurement system configuration #
    ####################################
    system_list = [] #holds the supported list of measurement systems 
    system_index = 1 #active measurement system (1 = system 1)

    #########################
    # communication devices #
    #########################
    com_serialautodetect = True #enable/disable automatic base station detection
    com_serialmax = 1 #maximum number of COM ports the application uses and tries to open
    com_serialdevs = [] #holds the configured serial ports (after initialization)
    com_serialbaud = 57600 #default serial baud rate to use -> this must be loaded for each specified port
    
    com_filesystem_inout = False #enable/disable file system communication support
    com_webserver_rest = False #enable/disable webserver communication support
   
       
    ########################################
    # system paths (filenames and folders) #
    ########################################
    #p  .. general path object
    #p_file_XXX .. filename definition (specific path) -> is automatically evaluated DEF_IDENTIFIER_FILE
    #p_file_dir .. directory name defintion (specific path) -> is automatically evaluated DEF_IDENTIFIER_DIR
    p_dir_app: str = os.path.abspath(CFG_APPDIR) #application directory
    p_dir_cfg : str = os.path.abspath(os.path.join(p_dir_app,"cfg/")) #application configuration file directory (*.ini setting file)
    p_dir_template: str = os.path.abspath(os.path.join(p_dir_app,"cfg/templates/")) #application configuration file directory (*.ini setting file)
    p_dir_tmp : str = os.path.abspath(os.path.join(p_dir_app,"tmp/")) #temporary files
    #p_file_appcfg : str = os.path.abspath(os.path.join(p_dir_cfg,appdef.INIFILES.APPCFG))

    p_file_about_cfg : str = os.path.abspath(os.path.join(p_dir_app,"libxkm/libprodat/aboutpopup_cfg.ini"))
    #p_file_cloudcfg : str = os.path.abspath(os.path.join(p_dir_cfg,appdef.INIFILES.CLOUDSYNC))
    p_dir_upload_zip : str = os.path.abspath(os.path.join(p_dir_app,"db/upload/")) #DB Upload
    p_dir_remote_upload : str = "/#shares/tmp/xkmupload" #remote uploadpath
    #database
    p_dir_db : str = os.path.abspath(os.path.join(p_dir_app,"db/")) #database folder
    p_dir_meas : str = os.path.abspath(os.path.join(p_dir_app,"db/meas/")) #database support folder for measurements
    p_dir_report : str = os.path.abspath(os.path.join(p_dir_app, "db/reports/")) #database support folder for reports
    p_dir_db_user: str = os.path.abspath(os.path.join(p_dir_app,"db/user.db")) #user database folder
    p_dir_db_data: str = os.path.abspath(os.path.join(p_dir_app,"db/xkm.db")) #xkm database folder
    p_dir_log : str = os.path.abspath(os.path.join(p_dir_app,"")) #xkm database folder
    p_dir_doc : str = os.path.abspath(os.path.join(p_dir_app,"doc/")) #documentation (generated) folder
    
    p_dir_media : str = os.path.abspath(os.path.join(p_dir_app,"media/"))
    p_dir_screenshot: str = os.path.abspath(os.path.join(p_dir_app, "screenshot/"))
    p_dir_media_icons : str = os.path.abspath(os.path.join(p_dir_app,"media/icon/"))
    p_dir_backup : str = os.path.abspath(os.path.join(p_dir_app,"backup/"))
    p_dir_media_iconapp : str = os.path.abspath(os.path.join(p_dir_media_icons,"prodat_128x128.ico"))

    p_file_log_user : str = os.path.abspath(os.path.join(p_dir_log, 'user.log'))
    p_file_log_system : str = os.path.abspath(os.path.join(p_dir_log, 'system.log'))

    ########################################
    # SETTINGS (attributes) WE WANT TO HAVE 
    ########################################
    _inicfg_sec_gui = []
    _inicfg_sec_general = ["system_index", "app_loginmode"]   #we don't need a mapper. use attribute names for ini files
    _inicfg_sec_userfields = ["userfields_encoding"]
    _inicfg_sec_version = ["version_appcfg"] #we can keep track of module version (i.e., for converting old ini files, if needed)
    
    #inifile default path and configuration
    def check(self):
        '''
        generalized wrapper function
        '''
        ret = []
        ret.append(self.check_path(exception=True, fix_errors=False))
        return ret
    
    def check_and_correct(self):
        '''
        generalized wrapper function -> automatically fix issues
        '''
        ret = []
        ret.append(self.check_path(exception=False, fix_errors=True))
        return ret
    
    
    def check_path(self, exception=True, fix_errors=False):
        '''
        sub check -> we are supporting different categories.
        running module checks: is everything as needed and expected:
            * we have all required system paths, correct if required
            * our inifiles contain the needed information, if not adjust
        check local path configuration, can we reach every ressource?
        @exception: if True throws exceptions on error
        @fix_errors: if True we try to fix errors automatically (typically for a second run, after having informed the user
        @returns: a report list
        '''
        
        #checking directories
        paths = [getattr(self,p) for p in self.__dict__ if DEF_IDENTIFIER_DIR in str(p)]
        ret = []
        for p in paths:
            if not os.path.exists(p):
                if exception: 
                    raise ValueError("appcfg:check: we are missing %s" % p)
                ret.append( (p, False) )
                
                if fix_errors:
                    os.makedirs(p)
                
            else:
                ret.append( (p, True))
        
        #checking files manually (we need doing this for some special files)
        if not os.path.exists(self.p_file_appcfg):
            if fix_errors: self.ini_default_appcfg(self.p_file_appcfg) #creating default file
            if exception: raise FileNotFoundError("Missing appcfg.ini file")
            ret.append([self.p_file_appcfg, False])
    
        #checking files automatically p_file_XXXX
        paths = [getattr(self,p) for p in self.__dict__ if DEF_IDENTIFIER_FILE in str(p)]
        ret = []
        
    
        for p in paths:
            if not os.path.exists(p):
                if exception: 
                    raise ValueError("appcfg:file: we are missing %s" % p)
                ret.append( (p, False) )
            else:
                ret.append( (p, True))
        return ret
    
       
    def ini_save(self, dirpath=None):
        '''
        save the application configuration settings into an *.ini file
        '''
        raise AssertionError("to implement")
    
        
    def ini_default_appcfg(self, path=None):
        '''
        create a default app ini configuration file 
        '''
        print("appcfg:ini_default: appcfg.ini with default settings created in %s" % path)
        if path == None: path = self.p_file_appcfg
        print("appcfg:ini_default: appcfg.ini with default settings created in %s" % path)
        #creating appcfg file at specified path
        cfgp = configparser.ConfigParser()
        cfgp.add_section(DEF_INISEC_GENERAL)
        for attr in self._inicfg_sec_general: cfgp[DEF_INISEC_GENERAL][attr] = str(getattr(self,attr))
        cfgp.add_section(DEF_INISEC_GUI)
        for attr in self._inicfg_sec_gui: cfgp[DEF_INISEC_GUI][attr] = str(getattr(self,attr))
        cfgp.add_section(DEF_INISEC_USERFIELDS)
        for attr in self._inicfg_sec_userfields: cfgp[DEF_INISEC_USERFIELDS][attr] = str(getattr(self,attr))
        cfgp.add_section(DEF_INISEC_VERSION) 
        for attr in self._inicfg_sec_version: cfgp[DEF_INISEC_VERSION][attr] = str(getattr(self,attr))
    
@dataclass
class AppConfigRKM(ConfigApp):
    '''
    RKM Application Configuration class -> alters and extends settings of AppConfig as needed in RKM
    '''
    pass

@dataclass
class AppConfigBKM(ConfigApp):
    '''
    BKM Application Configuration class -> alters and extends settings of AppConfig as needed in BKM
    '''
    pass

#################################
# DEFAULT CONFIGURATION OBJECTS #
#################################
CFG = ConfigApp() #create a general default configuration object

def test_usage_regular():
    mycfg = ConfigApp()
    print(str(mycfg))
    print(repr(mycfg))
    print("The path settings muss work, throw exceptions if a required ressource is missing")
    try:
        #must raise same Exceptions
        mycfg.check_path() 
        mycfg.check() #should be used outside the module
    except Exception as e:
        print(e) 
    
    print("Try to automatically solve issues and fix things")
    mycfg.check_and_correct()

    print(mycfg.check_path(exception=False))    
    
    print("LOGIN MODE OF APPLICATION:", mycfg.app_loginmode)
    
    print("In standalone mode we must have everything generated, as expected to run the application")
    mycfg.check_ini(exception=True)
    
    print("different app modes")
    print("APPMODE: ", CFG.appmode)
    print("APPNAME: ", CFG.appname)
    print("APPTITLE: ", CFG.apptitle)

if __name__ == '__main__':
    print ("appcfg.py - standalone tests and usage demonstration, as well as simple development testing")
    test_usage_regular()
    print("appcfg.py - done")