import PrismInit
from PrismUtils.Decorators import err_catcher as err_catcher

from pathlib import Path
import hou
import os

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from rockinvfx import lopGeneral
from pprint import pprint

# print('start of loprender.py')
from .interfaceUI.loprender_submit_ui import Ui_wg_LOP_render

##
# Main funcs
## 
def onNodeCreated(kwargs):
    # create state?    
    core = PrismInit.pcore
    sm = core.getStateManager()
    if not sm:
        return
    
    knode = kwargs['node']
    parent = getParentFolder() # makes the collapsible folder in statemanger
    plugin = core.appPlugin # get houdini plugin?
    stateType = "ImageRender" # is this correct?
    # print("hello updates?")
    renderer = "karma"
    state = sm.createState(stateType, node=knode, parent=parent)

    if parent:
        parent.setExpanded(parent.isExpanded())

def updateDescriptiveParm(node):
    me = node
    core = PrismInit.pcore    

    product = me.parm('identifier').evalAsString()
    version = core.versionFormat % me.parm('version').evalAsInt()
    context_str = me.parm('context').evalAsString()
    output_text = "{}\n{} - {}".format(context_str, product, version)    
    me.parm('descriptiveparm').set(output_text)


def submitToFarm(kwargs):
    '''
    Uses Prism' deadline plugin to submit to farm
    '''
    core = PrismInit.pcore
    deadline = core.getPlugin('Deadline')

def testFunc(kwargs):
    pass

def getDropdownMenu(kwargs):
    '''
    returns prism project's shots / assets based on incoming parameter 
    make sure tick "use token as value" on parameter menu
    '''
    # c = PrismInit.pcore
    me = kwargs['node']
    parm = kwargs['parm']
    
    core = PrismInit.pcore   
    out = []

    if parm.name().startswith("product"):
        entity = lopGeneral.getEntity(me, context_only=True)                
        names = core.products.getProductsFromEntity(entity)
        out = [entry['product'] for entry in names]

    if parm.name() == "identifier":
        entity = lopGeneral.getEntity(me, context_only=True)
        names = core.mediaProducts.getIdentifiersByType(entity)
        names = names['3d']
        out = [render['identifier'] for render in names]

    if parm.name() == "version":
        do_autoversion = me.parm('do_autoversion').evalAsInt()
        if not do_autoversion:
            entity = lopGeneral.getEntity(me, context_only=True)
            product_name = me.parm('identifier').evalAsString()
            # entity['product'] = product_name            
            entity['identifier'] = product_name
            find_versions = core.mediaProducts.getVersionsFromContext(entity)                         
            versions = [entry['version'] for entry in find_versions if entry['version']!="master"]   
            out = [int(version_string[1:]) for version_string in versions]

    if parm.name() == "context_sequence":
        context_type = me.parm("context_type").evalAsString()
        if context_type == "shot":
            seqs = core.entities.getSequences()
            out = seqs
        else:
            pass
        
    if parm.name() == "context_shot":
        sequence = me.parm('context_sequence').evalAsString()
        find_shots = core.entities.getShots(sequence, getSequences=False)
        shot_names = [entry['shot'] for entry in find_shots]
        out = shot_names

    if parm.name() == "context_asset":
        context_type = me.parm("context_type").evalAsString()
        if context_type == "asset":
            find_assets = core.entities.getAssets()
            asset_names = [entry['asset_path'] for entry in find_assets]
            out = asset_names
        
    pairs = list(zip(out,out))
    return [item for sublist in pairs for item in sublist]

def getFormats():    
    '''
    for format menu script
    '''
    ext = ['.exr', '.jpg', '.png']
    pairs = list(zip(ext,ext))
    return [item for sublist in pairs for item in sublist]

def makeExportPath(node):
    me = node
    core = PrismInit.pcore
    currentEntity = lopGeneral.getEntity(node, context_only=True)    
    entity = currentEntity

    if not currentEntity: # if empty e.g non prism scene        
        return "Not in Prism pipe"        
    
    if not lopGeneral.isContextDefined(entity):
        return ""
    # Parse interface parameters
    product = me.parm('identifier').evalAsString()
    ext = me.parm('format').evalAsString()
    do_autoversion = me.parm('do_autoversion').evalAsInt()
    version = None
    if not do_autoversion:        
        manual_version = me.parm('version').evalAsInt()
        version = core.versionFormat % manual_version
    else: # manually specify rather than use None
        _temp_entity = entity.copy()
        _temp_entity['identifier'] = product        
        _temp_version = core.mediaProducts.getVersionsFromIdentifier(_temp_entity)        
        latest = core.mediaProducts.getLatestVersionFromVersions(_temp_version)
        version = core.versionFormat % 1
        if latest:                        
            _temp_version = int(latest.get('version', '')[1:])
            _temp_version += 1
            version = core.versionFormat % _temp_version   
    
    fpadding = "$F%d" % core.framePadding    
    # print(entity)
    if entity['type'] == 'asset':
        # edge case where asset with folder had bad render path
        entity['asset'] = entity['asset_path'].split("\\")[-1] # asset required for generateMedia            
    path = core.mediaProducts.generateMediaProductPath(entity, task=product, extension=ext, framePadding=fpadding, version=version)    
    
    if path: # update manual version        
        data = core.mediaProducts.getDataFromFilepath(path)               
        # if weird case where asset version mixed with identifier, fix manually
        if entity['type'] == 'asset' and not data.get('version','')[1:].isdigit():
            _tmp_split = data.get('identifier','').split(os.path.sep)            
            data['identifier'] = _tmp_split[0]
            data['version'] = _tmp_split[-1]
        version = int(data.get('version', '')[1:])
        me.parm('version').set(version)

    replace_rvfx = True
    if replace_rvfx:
        path = lopGeneral.make_houdini_filepath_relative(path)
    
    updateDescriptiveParm(node)
    return path

def onExecute(kwargs):
    '''
    Handles different local execution paths
    When "Render to Disk" is pressed, local render.
    See onSubmitFarm for farm submission
    '''
    me = kwargs['node']    
    parm = kwargs['parm']
    core = PrismInit.pcore        

    # trigger update on version
    me.parm('version').pressButton()

    # if not me.inputs():
    #     core.popup("No inputs connected")
    #     return

    # Query output path and bake it (due to python expression recooking per frame)
    outputPath = me.parm('outputPath').evalAsString()
    if not outputPath:
        print('outputPath not valid')
        return
    me.parm('_path').set(outputPath)

    
    saveScene = bool(me.parm("saveScene").eval())
    incrementScene = saveScene and bool(
        me.parm("incrementScene").eval()
    )
    if saveScene:            
        if incrementScene:
            hou.hipFile.saveAndIncrementFileName()
        else:
            hou.hipFile.saveAndBackup()  
    
    if parm.name() == "execute":
        me.parm('usdrender_rop/execute').pressButton()
    elif parm.name() == "renderpreview":            
        me.parm('usdrender_rop/renderpreview').pressButton()
    elif parm.name() == "submit":
        submitter = Farm_Submitter(core, kwargs)
        submitter.show()
        me.parm('version').pressButton()

    # post job make versioninfo .json
    # createVersionInfo()
    # trigger refresh
    
    # export versioninfo.json
    # infoPath = core.mediaProducts.getMediaVersionInfoPathFromFilepath()  #products.getVersionInfoPathFromProductFilepath(outputPath)
    # details = versionInfoDetails(kwargs, outputPath)   
    # core.saveVersionInfo(filepath=infoPath, details=details)
    

def createVersionInfo(outputPath):
    '''
    TODO: take entity from path, create json
    '''
    core = PrismInit.pcore
    productType = "product"
    # export versioninfo.json
    if productType == "product":
        infoPath = core.products.getVersionInfoPathFromProductFilepath(outputPath)
    elif productType == "media":
        infoPath = core.mediaProducts.getMediaVersionInfoPathFromFilepath(outputPath)

    # entity = getEntity(me, context_only=False)    
    # details = entity.copy()    
    # details = versionInfoDetails(kwargs, outputPath)   
    # core.saveVersionInfo(filepath=infoPath, details=details)


class Farm_Submitter(QDialog):
    def __init__(self, core, kwargs):
        super(Farm_Submitter, self).__init__()
        # self.origin = origin
        # self.plugin = self.origin.plugin
        self.core = core
        self.plugin = core.appPlugin
        self.node = kwargs['node']
        self.deadline = core.getPlugin("Deadline")
        print("deadline plugin is:", self.deadline)
        self.core.parentWindow(self)        
        self.kwargs = kwargs
        self.showSm = False
        if self.core.sm.isVisible():
            self.core.sm.setHidden(True)
            self.showSm = True

        self.setupUi()
        self.initializeSettings()

    def setupUi(self):
        self.setWindowTitle("Prism Farm Submitter - %s" % self.node.path())
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        
        # Import UI file
        self.widgetui = QWidget()
        self.uifile = Ui_wg_LOP_render()
        self.uifile.setupUi(self.widgetui)
        # print("type of 1: ", type(self.uifile))
        # print("type of 2: ", type(self.widget))
        self.lo_main.addWidget(self.widgetui)                 
        
        # Hide unused ui elements
        self.uifile.gb_submit.setCheckable(False)
        if True:#self.uifile.cb_manager.count() == 1:
            self.uifile.f_manager.setVisible(False)
            self.uifile.gb_submit.setTitle('Submit to Deadline')#self.uifile.cb_manager.currentText())
        self.uifile.f_osPAssets.setVisible(False)
        self.uifile.gb_osSlaves.setVisible(False)
        self.uifile.w_dlConcurrentTasks.setVisible(False)
        self.uifile.w_dlGPUpt.setVisible(False)
        self.uifile.w_dlGPUdevices.setVisible(False)


        # Add deadline specific        
        self.setupUi_add_deadline_specific()

        # self.uifile.f_manager
        # IDK now
        # self.widgetui.w_name.setVisible(False)
        # self.widgetui.gb_previous.setHidden(True)
        # self.widgetui.gb_general.setVisible(False)

        

        self.b_submit = QPushButton("Submit")
        self.lo_main.addWidget(self.b_submit)
        self.b_submit.clicked.connect(self.submit)

    def setupUi_add_deadline_specific(self):
        '''
        Adds missing deadline parms we need
        Taken from prism_deadline_functions.py
        '''
        lo = self.uifile.gb_submit.layout() # get layout to add to

        self.w_machineLimit = QWidget()
        self.lo_machineLimit = QHBoxLayout()
        self.lo_machineLimit.setContentsMargins(9, 0, 9, 0)
        self.l_machineLimit = QLabel("Machine Limit:")
        self.sp_machineLimit = QSpinBox()
        self.sp_machineLimit.setMaximum(99999)
        self.w_machineLimit.setLayout(self.lo_machineLimit)
        self.lo_machineLimit.addWidget(self.l_machineLimit)
        self.lo_machineLimit.addStretch()
        self.lo_machineLimit.addWidget(self.sp_machineLimit)
        # self.sp_machineLimit.editingFinished.connect(self.stateManager.saveStatesToScene)
        lo.addWidget(self.w_machineLimit)

        self.w_dlPreset = QWidget()
        self.lo_dlPreset = QHBoxLayout()
        self.lo_dlPreset.setContentsMargins(9, 0, 9, 0)
        self.l_dlPreset = QLabel("Pool Preset:")
        self.cb_dlPreset = QComboBox()
        self.cb_dlPreset.setMinimumWidth(150)
        self.w_dlPreset.setLayout(self.lo_dlPreset)
        self.lo_dlPreset.addWidget(self.l_dlPreset)
        self.lo_dlPreset.addStretch()
        self.lo_dlPreset.addWidget(self.cb_dlPreset)
        presets = self.deadline.getDeadlinePoolPresets()
        self.cb_dlPreset.addItems(presets)
        self.cb_dlPreset.currentIndexChanged.connect(lambda x: self.deadline.presetChanged(self))
        lo.addWidget(self.w_dlPreset)

        self.w_dlPool = QWidget()
        self.lo_dlPool = QHBoxLayout()
        self.lo_dlPool.setContentsMargins(9, 0, 9, 0)
        self.l_dlPool = QLabel("Pool:")
        self.cb_dlPool = QComboBox()
        self.cb_dlPool.setToolTip("Deadline Pool (can be updated in the Prism Project Settings)")
        self.cb_dlPool.setMinimumWidth(150)
        self.w_dlPool.setLayout(self.lo_dlPool)
        self.lo_dlPool.addWidget(self.l_dlPool)
        self.lo_dlPool.addStretch()
        self.lo_dlPool.addWidget(self.cb_dlPool)
        self.cb_dlPool.addItems(self.deadline.getDeadlinePools())
        # self.cb_dlPool.activated.connect(self.stateManager.saveStatesToScene)
        lo.addWidget(self.w_dlPool)

        self.w_sndPool = QWidget()
        self.lo_sndPool = QHBoxLayout()
        self.lo_sndPool.setContentsMargins(9, 0, 9, 0)
        self.l_sndPool = QLabel("Secondary Pool:")
        self.cb_sndPool = QComboBox()
        self.cb_sndPool.setToolTip("Deadline Seconday Pool (can be updated in the Prism Project Settings)")
        self.cb_sndPool.setMinimumWidth(150)
        self.w_sndPool.setLayout(self.lo_sndPool)
        self.lo_sndPool.addWidget(self.l_sndPool)
        self.lo_sndPool.addStretch()
        self.lo_sndPool.addWidget(self.cb_sndPool)
        self.cb_sndPool.addItems(self.deadline.getDeadlinePools())
        # self.cb_sndPool.activated.connect(self.stateManager.saveStatesToScene)
        lo.addWidget(self.w_sndPool)

        self.w_dlGroup = QWidget()
        self.lo_dlGroup = QHBoxLayout()
        self.lo_dlGroup.setContentsMargins(9, 0, 9, 0)
        self.l_dlGroup = QLabel("Group:")
        self.cb_dlGroup = QComboBox()
        self.cb_dlGroup.setToolTip("Deadline Group (can be updated in the Prism Project Settings)")
        self.cb_dlGroup.setMinimumWidth(150)
        self.w_dlGroup.setLayout(self.lo_dlGroup)
        self.lo_dlGroup.addWidget(self.l_dlGroup)
        self.lo_dlGroup.addStretch()
        self.lo_dlGroup.addWidget(self.cb_dlGroup)
        self.cb_dlGroup.addItems(self.deadline.getDeadlineGroups())
        # self.cb_dlGroup.activated.connect(self.stateManager.saveStatesToScene)
        lo.addWidget(self.w_dlGroup)

        self.gb_prioJob = QGroupBox("Submit High Prio Job")
        self.gb_prioJob.setCheckable(True)
        self.gb_prioJob.setChecked(False)
        lo.addWidget(self.gb_prioJob)

        self.lo_prioJob = QVBoxLayout()
        self.gb_prioJob.setLayout(self.lo_prioJob)
        # self.gb_prioJob.toggled.connect(self.stateManager.saveStatesToScene)

        self.w_highPrio = QWidget()
        self.lo_highPrio = QHBoxLayout()
        self.l_highPrio = QLabel("Priority:")
        self.sp_highPrio = QSpinBox()
        self.sp_highPrio.setMaximum(100)
        self.sp_highPrio.setValue(70)
        self.lo_prioJob.addWidget(self.w_highPrio)
        self.w_highPrio.setLayout(self.lo_highPrio)
        self.lo_highPrio.addWidget(self.l_highPrio)
        self.lo_highPrio.addStretch()
        self.lo_highPrio.addWidget(self.sp_highPrio)
        self.lo_highPrio.setContentsMargins(0, 0, 0, 0)
        # self.sp_highPrio.editingFinished.connect(self.stateManager.saveStatesToScene)

        self.w_highPrioFrames = QWidget()
        self.lo_highPrioFrames = QHBoxLayout()
        self.l_highPrioFrames = QLabel("Frames:")
        self.e_highPrioFrames = QLineEdit()
        self.e_highPrioFrames.setText("{first}, {middle}, {last}")
        self.b_highPrioFrames = QToolButton()
        self.b_highPrioFrames.setArrowType(Qt.DownArrow)
        self.lo_prioJob.addWidget(self.w_highPrioFrames)
        self.w_highPrioFrames.setLayout(self.lo_highPrioFrames)
        self.lo_highPrioFrames.addWidget(self.l_highPrioFrames)
        self.lo_highPrioFrames.addStretch()
        self.lo_highPrioFrames.addWidget(self.e_highPrioFrames)
        self.lo_highPrioFrames.addWidget(self.b_highPrioFrames)
        self.lo_highPrioFrames.setContentsMargins(0, 0, 0, 0)
        # self.e_highPrioFrames.editingFinished.connect(
        #     self.stateManager.saveStatesToScene
        # )
        # self.b_highPrioFrames.clicked.connect(lambda x=None, s=state: self.showHighPrioJobPresets(s))

        # temp hide high prio job
        self.gb_prioJob.setHidden(True)
        self.label_osDependencies = self.uifile.label_19
        #self.uifile.label_19.setText("Include Auxiliary files") # set dependency label to change
        # self.uifile.f_osDependencies.setHidden(True) # hide submit dependent files
        self.uifile.f_osUpload.setHidden(True) # hide upload output        

        if presets:
            self.w_dlPool.setHidden(True)
            self.w_sndPool.setHidden(True)
            self.w_dlGroup.setHidden(True)
            self.presetChanged(self)
        else:
            self.w_dlPreset.setHidden(True)
    
    def initializeSettings(self):
        '''
        Extra customisations based on parameter input
        '''
        origin = self.uifile
        # UI adjustments
        do_husk = self.node.parm('do_husk').evalAsInt()
        
        if do_husk:
            origin.f_rjWidgetsPerTask.setHidden(True)
            self.label_osDependencies.setText("Submit USD with job")
            # print([child.objectName() for child in origin.gb_submit.children()])
            # framesPerTask = origin.gb_submit.findChild(QWidget, "f_rjWidgetsPerTask")
            # print(framesPerTask)                        
            #origin.gb_submit.f_rjFramesPerTask.setHidden(True)    
        else:
            self.label_osDependencies.setText("Submit Scenefile with job")

        # UI values
        project_name = Path(self.core.projectPath).name.lower()
        pools = self.deadline.getDeadlinePools()
        if project_name in pools:
            idx = pools.index(project_name)
            self.cb_dlPool.setCurrentIndex(idx)

    def closeEvent(self, event):
        ''' Idk what the purpose of this is, think its linked to state manager
        '''
        pass 

    def getOutputPath(self, hashes=True):
        '''
        Gets the path and expands it to absolute path
        '''
        #text = self.node.parm('outputPath').evalAsString()  
        text = self.node.parm('_path').unexpandedString()
        text = self.deadline.processHoudiniPath(self, text)
        if not hashes:
            text = text.replace('####', '$F4')
        return text      
    
    def getUsdRopOutputPath(self, render=False):
        '''
        Gets the path of the USD ROP when using husk
        '''
        usd_rop = self.node.node('usd_rop')
        # update datetime for random render folder
        from datetime import datetime
        time = datetime.now().strftime('%H:%M:%S.%f')[:-4]
        time = time.replace(':','').replace('.','')
        self.node.parm('_datetime').set(time)

        if render: # cant remember why we need this option
            usd_rop.parm('execute').pressButton()
        #text = self.node.parm('outputPath').evalAsString()  
        directory = usd_rop.parm('savetodirectory_directory').evalAsString()
        filename = usd_rop.parm('lopoutput').evalAsString()
        output = Path(directory, filename)        
        return output.as_posix()      
    
    def getUsdFilesToSubmit(self, usd_input_path):
        '''
        Finds any other aux files that our __render__ usd might depend on in the same folder
        '''
        filepath = Path(usd_input_path)
        folder = filepath.parent        
        files = list(Path(folder).glob('*'))
        files = [str(path) for path in files] # convert Path to windows str
        return files

    def createJobName(self):
        scenefileName = Path(self.core.getCurrentFileName(path=False)).stem        
        ropname = self.node.name()
        jobName = ('_').join([ropname, scenefileName])        
        return jobName
    
    def getFrameRange(self) -> str:
        '''
        Parses frame range parameters to generate deadline frame string
        '''
        frame_type = self.node.parm('trange').eval()
        if frame_type == 0: # current frame
            curr_frame = hou.frame()
            frameStr = "%s" % int(curr_frame)
        else:
            frame_tuple = self.node.parmTuple('f').eval()
            startFrame = int(frame_tuple[0])
            endFrame = int(frame_tuple[1])
            increment = frame_tuple[2]
            frameStr = "%s-%s" % (int(startFrame), int(endFrame))
            # todo logic for when increment < or > 1
            if increment != 1:
                pass
                
        return frameStr

    def createJobInfos(self) -> dict:
        '''
        Parses the UI and node for relevant information for job    
        '''
        origin = self.uifile

        # Parsing
        jobName = self.createJobName() #self.deadline.getJobName(details=None, origin=self)#"test"# func here
        jobnameSuffix = ""
        jobPool = self.cb_dlPool.currentText()
        jobSndPool = self.cb_sndPool.currentText()
        jobGroup = self.cb_dlGroup.currentText()
        jobPrio = origin.sp_rjPrio.value()
        jobTimeOut = str(origin.sp_rjTimeout.value())
        jobMachineLimit = str(self.sp_machineLimit.value())
        jobFramesPerTask = origin.sp_rjFramesPerTask.value()
        jobOutputFile = self.getOutputPath()
        frameStr = self.getFrameRange()        

        # Job info creation
        jobInfos = {}
        jobInfos["Name"] = jobName        

        if jobnameSuffix:
            jobInfos["Name"] += jobnameSuffix

        jobInfos["Pool"] = jobPool
        jobInfos["SecondaryPool"] = jobSndPool
        jobInfos["Group"] = jobGroup
        jobInfos["Priority"] = jobPrio
        jobInfos["TaskTimeoutMinutes"] = jobTimeOut
        jobInfos["MachineLimit"] = jobMachineLimit
        jobInfos["Frames"] = frameStr
        jobInfos["ChunkSize"] = jobFramesPerTask
        jobInfos["OutputFilename0"] = jobOutputFile

        self.deadline.addEnvironmentItem(jobInfos, "prism_project", self.core.prismIni.replace("\\", "/"))
        self.deadline.addEnvironmentItem(jobInfos, "prism_source_scene", self.core.getCurrentFileName())

        if os.getenv("PRISM_LAUNCH_ENV"):
            envData = self.core.configs.readJson(data=os.getenv("PRISM_LAUNCH_ENV"))
            for item in envData.items():
                self.deadline.addEnvironmentItem(jobInfos, item[0], item[1])

        do_batch = False
        jobBatchName = "replace_batch_name"
        if do_batch:
            jobInfos["BatchName"] = jobBatchName

        # if len(dependencies) > 0:
        #     depType = dependencies[0]["type"]
        #     jobInfos["IsFrameDependent"] = "false" if depType == "job" else "true"
        #     if depType in ["job", "frame"]:
        #         jobids = []
        #         for dep in dependencies:
        #             jobids += dep["jobids"]

        #         jobInfos["JobDependencies"] = ",".join(jobids)
        #         if depType == "frame":
        #             jobInfos["FrameDependencyOffsetStart"] = dependencies[0]["offset"]

        #     elif depType == "file":
        #         jobInfos["ScriptDependencies"] = os.path.abspath(
        #             os.path.join(os.path.dirname(__file__), "DeadlineDependency.py")
        #         )        
        return jobInfos
    
    def createPluginInfos(self) -> dict:
        '''
        Default Plugin info
        '''        
        pluginInfos = {}
        pluginInfos["Build"] = "64bit"

        return pluginInfos

    def setupHythonJob(self, dlParams, scenefile=None, submit_aux=False):
        '''
        Edits the dlParams dictionary in place
        '''
        homeDir = (self.deadline.CallDeadlineCommand(["-GetCurrentUserHomeDirectory"]))
        homeDir = homeDir.replace("\r", "").replace("\n", "")

        dlParams["pluginInfoFile"] = os.path.join(homeDir, "temp", "houdini_plugin_info.job")
        dlParams["jobInfoFile"] = os.path.join(homeDir, "temp", "houdini_submit_info.job")

        dlParams["jobInfos"]["Plugin"] = "Houdini"
        dlParams["jobInfos"]["Comment"] = "Prism-Submission-Houdini_%s" % "Karma"
        driver = self.node.node('usdrender_rop')        
        
        dlParams["pluginInfos"]["OutputDriver"] = driver.path()
        dlParams["pluginInfos"]["IgnoreInputs"] = "False"
        dlParams["pluginInfos"]["Version"] = self.plugin.getDeadlineHoudiniVersion()
        if submit_aux:
            dlParams["arguments"] = [scenefile]
        else:
            dlParams["pluginInfos"]["SceneFile"] = scenefile
        return dlParams

    def setupHuskJob(self, dlParams, renderer, usd_inputs=None, output_path=None, submit_aux=True):
        '''
        similar to setupHythonJob
        '''
        homeDir = self.deadline.CallDeadlineCommand(["-GetCurrentUserHomeDirectory"])
        homeDir = homeDir.replace("\r", "").replace("\n", "")

        dlParams["pluginInfoFile"] = os.path.join(homeDir, "temp", "houdini_plugin_info.job")
        dlParams["jobInfoFile"] = os.path.join(homeDir, "temp", "houdini_submit_info.job")

        dlParams["jobInfos"]["Plugin"] = "Husk"
        dlParams["jobInfos"]["Comment"] = "Prism-Submission-Houdini_%s" % "Husk"
        dlParams['jobInfos']['Name'] += "_husk"
        dlParams['jobInfos']["ChunkSize"] = 1

        # setup output files
        if "OutputFilename0" in dlParams["jobInfos"]:
            output = Path( self.getOutputPath(hashes=False) )             
            directory = output.parent.as_posix() + '/'
            filename = output.name
            # replace #### with udim style
            # filename = filename.replace('####', '<F4>')
            dlParams["jobInfos"]["OutputDirectory0"] = directory
            dlParams["jobInfos"]["OutputFilename0"] = filename        
        
        if submit_aux: # attach file to arguments
            if type(usd_inputs)!=list:
                usd_inputs = [usd_inputs]            
            dlParams["arguments"] = usd_inputs
        else: # plugin points to existing file
            dlParams["pluginInfos"]["USDInput"] = usd_inputs            
        
        dlParams["pluginInfos"]["project_name"] = Path(hou.text.expandString("$PRISMJOB")).name # for husk plugin
        # dlParams["pluginInfos"]["RvfxRelative"] = True # for husk plugin
        dlParams["pluginInfos"]["CommandLineOptions"] = "" # extra cmd line options
        dlParams["pluginInfos"]["Renderer"] = renderer

        # store search path env var
        current = hou.text.expandString("$PXR_AR_DEFAULT_SEARCH_PATH")
        current += "{}{}".format(os.pathsep, hou.text.expandString("$PRISMJOB"))
        self.deadline.addEnvironmentItem(dlParams["jobInfos"], "PXR_AR_DEFAULT_SEARCH_PATH", current)
        return dlParams

    def submit(self):
        '''
        We have to make our own job infos, similar to deadline.sm_render_submitJob
        Because we dont use statemanager interface, and that function assumes we do
        so we need to copy a lot of the logic
        '''
        self.hide()
        do_husk = self.node.parm('do_husk').evalAsInt()
        do_submit_aux = self.uifile.chb_osDependencies.isChecked()               
        
        infoPath = self.core.products.getVersionInfoPathFromProductFilepath(self.getOutputPath())        
        if do_husk:
            # ignoring prism's deadline submitScene option. assuming it wont be read elsewhere
            submitScene = do_submit_aux # and self.core.getConfig("deadline", "submitScenes", dft=True, config="project")        
        else:
            submitScene = do_submit_aux and self.core.getConfig("deadline", "submitScenes", dft=True, config="project")        
        # Setup default infos
        jobInfos = self.createJobInfos()        
        pluginInfos = self.createPluginInfos()                
        
        dlParams = {
            "jobInfos": jobInfos,
            "pluginInfos": pluginInfos,
            "jobInfoFile": "",
            "pluginInfoFile": "",
            "arguments": None, # files or [self.core.getCurrentFileName()],
        }
        # sceneDescription is a dictionary that holds functions / info for prism to decide what IFD to do, arnold mantra etc
        # func to modify dlParams. our own implementatin found in Prism_Houdini_Functions sm_render_getDeadlineParams
        # these do modify jobInfos internally because immutable dict

        if do_husk: # parse husk inputs
            renderer = self.node.parm('renderer').evalAsString()            
            outputPath = self.getOutputPath(hashes=False)
            do_custom_usd = self.node.parm('dorenderexisting').evalAsInt()
            if do_custom_usd:
                usd_input = self.node.parm('renderexisting').evalAsString()                  
            else:                
                usd_input = self.getUsdRopOutputPath(render=True)  # bake out usd
                usd_input = self.getUsdFilesToSubmit(usd_input)
            dlParams = self.setupHuskJob(dlParams, renderer, usd_inputs=usd_input, output_path=outputPath, submit_aux=do_submit_aux)           
            # print("check file exists?", Path(dlParams['arguments'][0]).exists())
        else: # hython job
            scenefile = self.core.getCurrentFileName()
            dlParams = self.setupHythonJob(dlParams, scenefile=scenefile, submit_aux=do_submit_aux)

        arguments = []
        arguments.append(dlParams["jobInfoFile"])
        arguments.append(dlParams["pluginInfoFile"])

        # deadline takes auxillary files as arguments, hence this is a list of files.
        if submitScene:
            if dlParams["arguments"]:
                for arg in dlParams["arguments"]:
                    arguments.append(arg)        
        # pprint(jobInfos)
        # pprint(pluginInfos)
        # pprint(arguments)               
        
        # submission part
        result = None
        jobId = None
        skipSubmission = False # why would you want this?
        if not skipSubmission:
            result = self.deadline.deadlineSubmitJob(jobInfos, pluginInfos, arguments)            
            jobId = self.deadline.getJobIdFromSubmitResult(result)       

        if result:
            print(result)
            msg = "Job submitted successfully."
            self.core.popup(msg, severity="info")

        self.close()


