bl_info = {
    "name": "Blend_My_NFTs",
    "author": "Torrin Leonard, This Cozy Studio Inc",
    "version": (4, 0, 2),
    "blender": (3, 2, 0),
    "location": "View3D",
    "description": "An open source, free to use Blender add-on that enables you to create thousands of unique images, animations, and 3D models.",
    "category": "Development",
}

BMNFTS_VERSION = "v4.0.2"
LAST_UPDATED = "8:19AM, May 31st, 2022"

# ======== Import handling ======== #

import bpy
from bpy.app.handlers import persistent
from bpy.props import (IntProperty,
                       BoolProperty,
                       CollectionProperty)

import os
import sys
import json
import importlib
from dataclasses import dataclass
from typing import Any

# "a little hacky bs" - matt159 ;)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from main import \
    Checks, \
    DNA_Generator, \
    Exporter, \
    get_combinations, \
    HeadlessUtil, \
    Intermediate, \
    loading_animation, \
    Logic, \
    Material_Generator, \
    Metadata, \
    Rarity, \
    Refactorer

from UILists import \
    Custom_Metadata_UIList, \
    Logic_UIList

if "bpy" in locals():
    modules = {
        "Checks": Checks,
        "DNA_Generator": DNA_Generator,
        "Exporter": Exporter,
        "get_combinations": get_combinations,
        "HeadlessUtil": HeadlessUtil,
        "loading_animation": loading_animation,
        "Intermediate": Intermediate,
        "Logic": Logic,
        "Material_Generator": Material_Generator,
        "Metadata": Metadata,
        "Rarity": Rarity,
        "Refactorer": Refactorer,
        "Custom_Metadata_UIList": Custom_Metadata_UIList,
        "Logic_UIList": Logic_UIList,
    }

    for i in modules:
        if i in locals():
            importlib.reload(modules[i])

# ======== Persistant UI Refresh ======== #

# Used for updating text and buttons in UI panels
combinations: int = 0
recommended_limit: int = 0

@dataclass
class BMNFTData:
    nftName: str
    save_path: str
    nftsPerBatch: int
    batchToGenerate: int
    collectionSize: int

    Blend_My_NFTs_Output: str
    batch_json_save_path: str
    nftBatch_save_path: str

    enableImages: bool
    imageFileFormat: str

    enableAnimations: bool
    animationFileFormat: str

    enableModelsBlender: bool
    modelFileFormat: str

    enableCustomFields: bool

    cardanoMetaDataBool: bool
    solanaMetaDataBool: bool
    erc721MetaData: bool

    cardano_description: str
    solana_description: str
    erc721_description: str

    enableMaterials: bool
    materialsFile: str

    enableLogic: bool
    enable_Logic_Json: bool
    logicFile: str

    enableRarity: bool

    custom_Fields: dict = None
    fail_state: Any = False
    failed_batch: Any = None
    failed_dna: Any = None
    failed_dna_index: Any = None

    def __post_init__(self):
        self.custom_Fields = {}

def getBMNFTData():
    _save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)
    _Blend_My_NFTs_Output, _batch_json_save_path, _nftBatch_save_path = make_directories(_save_path)
    
    data = BMNFTData (
        nftName                 = bpy.context.scene.input_tool.nftName,
        save_path               = _save_path,
        nftsPerBatch            = bpy.context.scene.input_tool.nftsPerBatch,
        batchToGenerate         = bpy.context.scene.input_tool.batchToGenerate,
        collectionSize          = bpy.context.scene.input_tool.collectionSize,

        enableRarity            = bpy.context.scene.input_tool.enableRarity,

        Blend_My_NFTs_Output    = _Blend_My_NFTs_Output,
        batch_json_save_path    = _batch_json_save_path,
        nftBatch_save_path      = _nftBatch_save_path,

        enableLogic             = bpy.context.scene.input_tool.enableLogic,
        enable_Logic_Json       = bpy.context.scene.input_tool.enable_Logic_Json,
        logicFile               = bpy.context.scene.input_tool.logicFile,

        enableImages            = bpy.context.scene.input_tool.imageBool,
        imageFileFormat         = bpy.context.scene.input_tool.imageEnum,

        enableAnimations        = bpy.context.scene.input_tool.animationBool,
        animationFileFormat     = bpy.context.scene.input_tool.animationEnum,

        enableModelsBlender     = bpy.context.scene.input_tool.modelBool,
        modelFileFormat         = bpy.context.scene.input_tool.modelEnum,

        enableCustomFields      = bpy.context.scene.input_tool.enableCustomFields,

        cardanoMetaDataBool     = bpy.context.scene.input_tool.cardanoMetaDataBool,
        solanaMetaDataBool      = bpy.context.scene.input_tool.solanaMetaDataBool,
        erc721MetaData          = bpy.context.scene.input_tool.erc721MetaData,

        cardano_description     = bpy.context.scene.input_tool.cardano_description,
        solana_description      = bpy.context.scene.input_tool.solana_description,
        erc721_description      = bpy.context.scene.input_tool.erc721_description,

        enableMaterials         = bpy.context.scene.input_tool.enableMaterials,
        materialsFile           = bpy.path.abspath(bpy.context.scene.input_tool.materialsFile)
    )

    return data

@persistent
def Refresh_UI(dummy1, dummy2):
    """
    Refreshes the UI upon user interacting with Blender (using depsgraph_update_post handler). Might be a better handler
    to use.
    """
    global combinations
    global recommended_limit

    combinations = (get_combinations.get_combinations())
    recommended_limit = int(round(combinations / 2))

    # Add panel classes that require refresh to this refresh_panels tuple:
    refresh_panel_classes = (
        BMNFTS_PT_CreateData,
    )

    def redraw_panel(refresh_panel_classes):
        for i in refresh_panel_classes:
            try:
                bpy.utils.unregister_class(i)
            except:
                pass
            bpy.utils.register_class(i)

    redraw_panel(refresh_panel_classes)


bpy.app.handlers.depsgraph_update_post.append(Refresh_UI)


# ======== Helper functions ======== #
def make_directories(save_path):
    """Makes all Blend_My_NFTs Output folder directories from save_path input."""
    Blend_My_NFTs_Output = os.path.join(save_path, "Blend_My_NFTs Output", "NFT_Data")
    batch_json_save_path = os.path.join(Blend_My_NFTs_Output, "Batch_Data")

    nftBatch_save_path = os.path.join(save_path, "Blend_My_NFTs Output", "Generated NFT Batches")

    if not os.path.exists(Blend_My_NFTs_Output):
        os.makedirs(Blend_My_NFTs_Output)
    if not os.path.exists(batch_json_save_path):
        os.makedirs(batch_json_save_path)
    if not os.path.exists(nftBatch_save_path):
        os.makedirs(nftBatch_save_path)
    return Blend_My_NFTs_Output, batch_json_save_path, nftBatch_save_path


def runAsHeadless():
    """
    For use when running from the command line.
    """
    
    # force CUDA device usage with cycles renderer
    cprefs = bpy.context.preferences.addons['cycles'].preferences
    cprefs.compute_device_type = 'CUDA'
    cprefs.get_devices()
    print(cprefs.devices.keys())

    for key in cprefs.devices.keys():
            cprefs.devices[key].use = True

    print('Using {} devices for rendering!'.format(cprefs.get_num_gpu_devices()))

    def dumpSettings(settings):
        output = (
            f"nftName={             settings.nftName                    }\n"
            f"collectionSize={      str(settings.collectionSize)        }\n"
            f"nftsPerBatch={        str(settings.nftsPerBatch)          }\n"
            f"save_path={           settings.save_path                  }\n"
            f"enableRarity={        (settings.enableRarity)             }\n"
            f"enableLogic={         str(settings.enableLogic)           }\n"
            f"imageBool={           str(settings.imageBool)             }\n"
            f"imageEnum={           settings.imageEnum                  }\n"
            f"animationBool={       str(settings.animationBool)         }\n"
            f"animationEnum={       settings.animationEnum              }\n"
            f"modelBool={           str(settings.modelBool)             }\n"
            f"modelEnum={           settings.modelEnum                  }\n"
            f"batchToGenerate={     str(settings.batchToGenerate)       }\n"
            f"cardanoMetaDataBool={ str(settings.cardanoMetaDataBool)   }\n"
            f"cardano_description={ settings.cardano_description        }\n"
            f"erc721MetaData={      str(settings.erc721MetaData)        }\n"
            f"erc721_description={  settings.erc721_description         }\n"
            f"solanaMetaDataBool={  str(settings.solanaMetaDataBool)    }\n"
            f"solana_description={  settings.solana_description         }\n"
            f"enableCustomFields={  str(settings.enableCustomFields)    }\n"
            f"customfieldsFile={    settings.customfieldsFile           }\n"
            f"enableMaterials={     str(settings.customfieldsFile)      }\n"
            f"materialsFile={       settings.materialsFile              }\n"
        )
        print(output)

    args, parser = HeadlessUtil.getPythonArgs()

    settings = bpy.context.scene.input_tool

    # dumpSettings(settings)

    with open(args.config_path, 'r') as f:
        configs = [line.strip() for line in f.readlines() if not (line[0] == '#' or len(line.strip()) < 1)]

        pairs = [config.strip().split('=') for config in configs]

        # print(pairs)

        settings.nftName                = pairs[0][1]
        settings.collectionSize         = int(pairs[1][1])
        settings.nftsPerBatch           = int(pairs[2][1])
        settings.save_path              = pairs[3][1]
        settings.enableRarity           = pairs[4][1] == 'True'
        settings.enableLogic            = pairs[5][1] == 'True'
        settings.enableLogicJson        = pairs[6][1] == 'True'
        settings.logicFile              = pairs[7][1]
        settings.imageBool              = pairs[8][1] == 'True'
        settings.imageEnum              = pairs[9][1]
        settings.animationBool          = pairs[10][1] == 'True'
        settings.animationEnum          = pairs[11][1]
        settings.modelBool              = pairs[12][1] == 'True'
        settings.modelEnum              = pairs[13][1]
        settings.batchToGenerate        = int(pairs[14][1])
        settings.cardanoMetaDataBool    = pairs[15][1] == 'True'
        settings.cardano_description    = pairs[16][1]
        settings.erc721MetaData         = pairs[17][1] == 'True'
        settings.erc721_description     = pairs[18][1]
        settings.solanaMetaDataBool     = pairs[19][1] == 'True'
        settings.solanaDescription      = pairs[20][1]
        settings.enableCustomFields     = pairs[21][1] == 'True'
        settings.customfieldsFile       = pairs[22][1]
        settings.enableMaterials        = pairs[23][1] == 'True'
        settings.materialsFile          = pairs[24][1]

    if args.save_path:
        settings.save_path = args.save_path

    if args.batch_number:
        settings.batchToGenerate = args.batch_number

    input = getBMNFTData()

    if args.batch_data_path:
        input.batch_json_save_path = args.batch_data_path

    if args.operation == 'create-dna':
        Intermediate.send_To_Record_JSON(input)

    elif args.operation == 'generate-nfts':
        Exporter.render_and_save_NFTs(input)

    elif args.operation == 'refactor-batches':
        Refactorer.reformatNFTCollection(input)


# ======== User input Property Group ======== #
class BMNFTS_PGT_Input_Properties(bpy.types.PropertyGroup):
    # Create NFT Data Panel:

    nftName: bpy.props.StringProperty(name="NFT Name")

    collectionSize: bpy.props.IntProperty(name="NFT Collection Size", default=1, min=1)  # max=(combinations - offset)
    nftsPerBatch: bpy.props.IntProperty(name="NFTs Per Batch", default=1, min=1)  # max=(combinations - offset)

    save_path: bpy.props.StringProperty(
        name="Save Path",
        description="Save path for NFT files",
        default="",
        maxlen=1024,
        subtype="DIR_PATH"
    )

    enableRarity: bpy.props.BoolProperty(name="Enable Rarity")

    enableLogic: bpy.props.BoolProperty(name="Enable Logic")
    enable_Logic_Json: bpy.props.BoolProperty(name="Use Logic.json instead")
    logicFile: bpy.props.StringProperty(
        name="Logic File Path",
        description="Path where Logic.json is located.",
        default="",
        maxlen=1024,
        subtype="FILE_PATH"
    )

    enableMaterials: bpy.props.BoolProperty(name="Enable Materials")
    materialsFile: bpy.props.StringProperty(
        name="Materials File",
        description="Path where Materials.json is located.",
        default="",
        maxlen=1024,
        subtype="FILE_PATH"
    )

    # Generate NFTs Panel:
    imageBool: bpy.props.BoolProperty(name="Image")
    imageEnum: bpy.props.EnumProperty(
        name="Image File Format",
        description="Select Image file format",
        items=[
            ('PNG', ".PNG", "Export NFT as PNG"),
            ('JPEG', ".JPEG", "Export NFT as JPEG")
        ]
    )

    animationBool: bpy.props.BoolProperty(name="Animation")
    animationEnum: bpy.props.EnumProperty(
        name="Animation File Format",
        description="Select Animation file format",
        items=[
            ('AVI_JPEG', '.avi (AVI_JPEG)', 'Export NFT as AVI_JPEG'),
            ('AVI_RAW', '.avi (AVI_RAW)', 'Export NFT as AVI_RAW'),
            ('FFMPEG', '.mkv (FFMPEG)', 'Export NFT as FFMPEG'),
            ('MP4', '.mp4', 'Export NFT as .mp4'),
            ('PNG', '.png', 'Export NFT as PNG'),
            ('TIFF', '.tiff', 'Export NFT as TIFF')
        ]
    )

    modelBool: bpy.props.BoolProperty(name="3D Model")
    modelEnum: bpy.props.EnumProperty(
        name="3D Model File Format",
        description="Select 3D Model file format",
        items=[
            ('GLB', '.glb', 'Export NFT as .glb'),
            ('GLTF_SEPARATE', '.gltf + .bin + textures',
             'Export NFT as .gltf with separated textures in .bin + textures.'),
            ('GLTF_EMBEDDED', '.gltf', 'Export NFT as embedded .gltf file that contains textures.'),
            ('FBX', '.fbx', 'Export NFT as .fbx'),
            ('OBJ', '.obj', 'Export NFT as .obj'),
            ('X3D', '.x3d', 'Export NFT as .x3d'),
            ('STL', '.stl', 'Export NFT as .stl'),
            ('VOX', '.vox (Experimental)',
             'Export NFT as .vox, requires the voxwriter add on: https://github.com/Spyduck/voxwriter')
        ]
    )

    batchToGenerate: bpy.props.IntProperty(name="Batch To Generate", default=1,
                                           min=1)

    # Refactor Batches & Create Metadata Panel:
    cardanoMetaDataBool: bpy.props.BoolProperty(name="Cardano Cip")
    cardano_description: bpy.props.StringProperty(name="Cardano description")

    solanaMetaDataBool: bpy.props.BoolProperty(name="Solana Metaplex")
    solana_description: bpy.props.StringProperty(name="Solana description")

    erc721MetaData: bpy.props.BoolProperty(name="ERC721")
    erc721_description: bpy.props.StringProperty(name="ERC721 description")

    enableCustomFields: bpy.props.BoolProperty(name="Enable Custom Metadata Fields")
    customfieldsFile: bpy.props.StringProperty(
        name="Custom Fields File",
        description="Path where Custom_Fields.json is located.",
        default="",
        maxlen=1024,
        subtype="FILE_PATH"
    )

    # Other Panel:

    # API Panel properties:
    apiKey: bpy.props.StringProperty(name="API Key", subtype='PASSWORD')


# ======== Main Operators ======== #
class createData(bpy.types.Operator):
    bl_idname = 'create.data'
    bl_label = 'Create Data'
    bl_description = 'Creates NFT Data. Run after any changes were made to scene. All previous data will be overwritten and cannot be recovered.'
    bl_options = {"REGISTER", "UNDO"}

    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")

    def execute(self, context):
        # Handling Custom Fields UIList input:
        input = getBMNFTData()

        if input.enableLogic:
            if input.enable_Logic_Json and not input.logicFile:
                self.report({'ERROR'}, f"No Logic.json file path set. Please set the file path to your Logic.json file.")

        Intermediate.send_To_Record_JSON(input)
                        
        self.report({'INFO'}, f"NFT Data created!")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class exportNFTs(bpy.types.Operator):
    bl_idname = 'exporter.nfts'
    bl_label = 'Export NFTs'
    bl_description = 'Generate and export a given batch of NFTs.'
    bl_options = {"REGISTER", "UNDO"}

    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")

    def execute(self, context):

        input = getBMNFTData()
        # Handling Custom Fields UIList input:
        
        Intermediate.render_and_save_NFTs(input)

        self.report({'INFO'}, f"All NFTs generated for batch {input.batchToGenerate}!")

        return {"FINISHED"}


class resume_failed_batch(bpy.types.Operator):
    bl_idname = 'exporter.resume_nfts'
    bl_label = 'Resume Failed Batch'
    bl_description = 'Failed Batch detected. Generate NFTs where the previous batch failed?'
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        _save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)
        _Blend_My_NFTs_Output, _batch_json_save_path, _nftBatch_save_path = make_directories(_save_path)

        _batchToGenerate = bpy.context.scene.input_tool.batchToGenerate

        file_name = os.path.join(_batch_json_save_path, "Batch{}.json".format(_batchToGenerate))
        batchData = json.load(open(file_name))

        _fail_state, _failed_batch, _failed_dna, _failed_dna_index = Checks.check_FailedBatches(_batch_json_save_path)

        input = BMNFTData (
            nftName                 = batchData["Generation Save"][-1]["Render_Settings"]["nftName"],
            save_path               = _save_path,
            collectionSize          = batchData["Generation Save"][-1]["Render_Settings"]["collectionSize"],

            Blend_My_NFTs_Output    = _Blend_My_NFTs_Output,
            batch_json_save_path    = _batch_json_save_path,
            nftBatch_save_path      = batchData["Generation Save"][-1]["Render_Settings"]["nftBatch_save_path"],

            enableImages            = batchData["Generation Save"][-1]["Render_Settings"]["enableImages"],
            imageFileFormat         = batchData["Generation Save"][-1]["Render_Settings"]["imageFileFormat"],

            enableAnimations        = batchData["Generation Save"][-1]["Render_Settings"]["enableAnimations"],
            animationFileFormat     = batchData["Generation Save"][-1]["Render_Settings"]["animationFileFormat"],

            enableModelsBlender     = batchData["Generation Save"][-1]["Render_Settings"]["enableModelsBlender"],
            modelFileFormat         = batchData["Generation Save"][-1]["Render_Settings"]["modelFileFormat"],

            enableCustomFields      = batchData["Generation Save"][-1]["Render_Settings"]["enableCustomFields"],
            custom_Fields           = batchData["Generation Save"][-1]["Render_Settings"]["custom_Fields"],

            cardanoMetaDataBool     = batchData["Generation Save"][-1]["Render_Settings"]["cardanoMetaDataBool"],
            solanaMetaDataBool      = batchData["Generation Save"][-1]["Render_Settings"]["solanaMetaDataBool"],
            erc721MetaData          = batchData["Generation Save"][-1]["Render_Settings"]["erc721MetaData"],

            cardano_description     = batchData["Generation Save"][-1]["Render_Settings"]["cardano_description"],
            solana_description      = batchData["Generation Save"][-1]["Render_Settings"]["solana_description"],
            erc721_description      = batchData["Generation Save"][-1]["Render_Settings"]["erc721_description"],

            enableMaterials         = batchData["Generation Save"][-1]["Render_Settings"]["enableMaterials"],
            materialsFile           = batchData["Generation Save"][-1]["Render_Settings"]["materialsFile"],

            fail_state              = _fail_state,
            failed_batch            = _failed_batch,
            failed_dna              = _failed_dna,
            failed_dna_index        = _failed_dna_index
        )

        Exporter.render_and_save_NFTs(input)

        self.report({'INFO'}, f"Resuming Failed Batch Generation!")

        return {"FINISHED"}


class refactor_Batches(bpy.types.Operator):
    """Refactor your collection? This action cannot be undone."""
    bl_idname = 'refactor.batches'
    bl_label = 'Refactor your Batches?'
    bl_description = 'This action cannot be undone.'
    bl_options = {'REGISTER', 'INTERNAL'}

    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")

    def execute(self, context):
        # Passing info to main functions for refactoring:
        Refactorer.reformatNFTCollection(getBMNFTData())
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class export_settings(bpy.types.Operator):
    """Export your settings into a configuration file."""
    bl_idname = 'export.settings'
    bl_label = 'Export Settings'
    bl_description = 'Save your settings to a configuration file'
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)
        filename = "config.cfg"

        settings = bpy.context.scene.input_tool

        with open(save_path + filename, 'w') as config:
            output = (
                "#This file was auto-generated from the Blend_My_NFTs addon and is used\n"
                "#when running Blend_My_NFTs in a headless environment.\n"
                "\n"
                "#The name of your nft project\n"
                f"nftName={                 settings.nftName                    }\n"
                "\n"
                "#NFT Collection Size\n"
                f"collectionSize={          settings.collectionSize             }\n"
                "\n"
                "#The number of NFTs to generate per batch\n"
                f"nftsPerBatch={            str(settings.nftsPerBatch)          }\n"
                "\n"
                "#Save path for your NFT files\n"
                f"save_path={               settings.save_path                  }\n"
                "\n"
                "#Enable Rarity\n"
                f"enableRarity={            (settings.enableRarity)             }\n"
                "\n"
                "#Enable Logic\n"
                f"enableLogic={             str(settings.enableLogic)           }\n"
                f"enableLogicJson={         str(settings.enable_Logic_Json)     }\n"
                f"logicFilePath={           settings.logicFile                  }\n"
                "\n"
                "#NFT Media output type(s):\n"
                f"imageBool={               str(settings.imageBool)             }\n"
                f"imageEnum={               settings.imageEnum                  }\n"
                f"animationBool={           str(settings.animationBool)         }\n"
                f"animationEnum={           settings.animationEnum              }\n"
                f"modelBool={               str(settings.modelBool)             }\n"
                f"modelEnum={               settings.modelEnum                  }\n"
                "\n"
                "#Batch to generate\n"
                f"batchToGenerate={         str(settings.batchToGenerate)       }\n"
                "\n"
                "#Metadata Format\n"
                f"cardanoMetaDataBool={     str(settings.cardanoMetaDataBool)   }\n"
                f"cardano_description={     settings.cardano_description        }\n"
                f"erc721MetaData={          str(settings.erc721MetaData)        }\n"
                f"erc721_description={      settings.erc721_description         }\n"
                f"solanaMetaDataBool={      str(settings.solanaMetaDataBool)    }\n"
                f"solana_description={      settings.solana_description         }\n"
                "\n"
                "#Enable Custom Fields\n"
                f"enableCustomFields={      str(settings.enableCustomFields)    }\n"
                f"customfieldsFile={        settings.customfieldsFile           }\n"
                "\n"
                "#Enable Materials\n"
                f"enableMaterials={         str(settings.enableMaterials)       }\n"
                f"materialsFile={           settings.materialsFile              }\n"
            )

            print(output, file=config)

        self.report({'INFO'}, f"Saved settings to: {save_path + filename}!")

        return {"FINISHED"}


# ======== UI Panels ======== #
class BMNFTS_PT_CreateData(bpy.types.Panel):
    bl_label = "Create NFT Data"
    bl_idname = "BMNFTS_PT_CreateData"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blend_My_NFTs'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_scene = scene.input_tool

        row = layout.row()
        row.prop(input_tool_scene, "nftName")

        row = layout.row()
        layout.label(text=f"Maximum Number Of NFTs: {combinations}")
        layout.label(text=f"Recommended limit: {recommended_limit}")

        row = layout.row()
        row.prop(input_tool_scene, "collectionSize")

        row = layout.row()
        row.prop(input_tool_scene, "nftsPerBatch")

        row = layout.row()
        row.prop(input_tool_scene, "save_path")

        row = layout.row()
        row.prop(input_tool_scene, "enableRarity")

        row = layout.row()
        row.prop(input_tool_scene, "enableLogic")

        # Logic_UIList implementation:
        if bpy.context.scene.input_tool.enableLogic:
            layout = self.layout
            scn = bpy.context.scene

            rows = 2
            row = layout.row()
            row.template_list("CUSTOM_UL_logic_items", "", scn, "logic_fields", scn,
                              "logic_fields_index", rows=rows)

            col = row.column(align=True)
            col.operator("logic_uilist.logic_list_action", icon='ZOOM_IN', text="").action = 'ADD'
            col.operator("logic_uilist.logic_list_action", icon='ZOOM_OUT', text="").action = 'REMOVE'
            col.separator()
            col.operator("logic_uilist.logic_list_action", icon='TRIA_UP', text="").action = 'UP'
            col.operator("logic_uilist.logic_list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

            row = layout.row()
            col = row.column(align=True)
            row = col.row(align=True)
            row.operator("logic_uilist.logic_clear_list", icon="X")
            row = col.row(align=True)
            row.label(text=f"*Field Names must be unique.")

            row = layout.row()
            row.prop(input_tool_scene, "enable_Logic_Json")

            if bpy.context.scene.input_tool.enable_Logic_Json:
                row = layout.row()
                row.prop(input_tool_scene, "logicFile")

        row = layout.row()
        row.prop(input_tool_scene, "enableMaterials")

        if bpy.context.scene.input_tool.enableMaterials:
            row = layout.row()
            row.prop(input_tool_scene, "materialsFile")

        row = layout.row()
        self.layout.operator("create.data", icon='DISCLOSURE_TRI_RIGHT', text="Create Data")
        row = layout.row()
        layout.label(text=f"{BMNFTS_VERSION}")


class BMNFTS_PT_GenerateNFTs(bpy.types.Panel):
    bl_label = "Generate NFTs & Create Metadata"
    bl_idname = "BMNFTS_PT_GenerateNFTs"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blend_My_NFTs'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_scene = scene.input_tool

        row = layout.row()
        layout.label(text="NFT Media files:")

        row = layout.row()
        row.prop(input_tool_scene, "imageBool")
        if bpy.context.scene.input_tool.imageBool:
            row.prop(input_tool_scene, "imageEnum")

        row = layout.row()
        row.prop(input_tool_scene, "animationBool")
        if bpy.context.scene.input_tool.animationBool:
            row.prop(input_tool_scene, "animationEnum")

        row = layout.row()
        row.prop(input_tool_scene, "modelBool")
        if bpy.context.scene.input_tool.modelBool:
            row.prop(input_tool_scene, "modelEnum")

        row = layout.row()
        layout.label(text="Meta Data format:")

        row = layout.row()
        row.prop(input_tool_scene, "cardanoMetaDataBool")
        if bpy.context.scene.input_tool.cardanoMetaDataBool:
            row = layout.row()
            row.prop(input_tool_scene, "cardano_description")

            row = layout.row()
            row.operator("wm.url_open", text="Cardano Metadata Documentation",
                         icon='URL').url = "https://cips.cardano.org/cips/cip25/"

        row = layout.row()
        row.prop(input_tool_scene, "solanaMetaDataBool")
        if bpy.context.scene.input_tool.solanaMetaDataBool:
            row = layout.row()
            row.prop(input_tool_scene, "solana_description")

            row = layout.row()
            row.operator("wm.url_open", text="Solana Metadata Documentation",
                         icon='URL').url = "https://docs.metaplex.com/token-metadata/specification"

        row = layout.row()
        row.prop(input_tool_scene, "erc721MetaData")
        if bpy.context.scene.input_tool.erc721MetaData:
            row = layout.row()
            row.prop(input_tool_scene, "erc721_description")

            row = layout.row()
            row.operator("wm.url_open", text="ERC721 Metadata Documentation",
                         icon='URL').url = "https://docs.opensea.io/docs/metadata-standards"

        row = layout.row()
        row.prop(input_tool_scene, "enableCustomFields")

        # Custom Metadata Fields UIList:
        if bpy.context.scene.input_tool.enableCustomFields:
            layout = self.layout
            scn = bpy.context.scene

            rows = 2
            row = layout.row()
            row.template_list("CUSTOM_UL_custom_metadata_fields_items", "", scn, "custom_metadata_fields", scn, "custom_metadata_fields_index", rows=rows)

            col = row.column(align=True)
            col.operator("custom_metadata_fields_uilist.list_action", icon='ZOOM_IN', text="").action = 'ADD'
            col.operator("custom_metadata_fields_uilist.list_action", icon='ZOOM_OUT', text="").action = 'REMOVE'
            col.separator()
            col.operator("custom_metadata_fields_uilist.list_action", icon='TRIA_UP', text="").action = 'UP'
            col.operator("custom_metadata_fields_uilist.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

            row = layout.row()
            col = row.column(align=True)
            row = col.row(align=True)
            row.label(text=f"*Field Names must be unique.")
            row = col.row(align=True)
            row.operator("custom_metadata_fields_uilist.clear_list", icon="X")

        row = layout.row()
        row.prop(input_tool_scene, "batchToGenerate")

        save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)
        Blend_My_NFTs_Output = os.path.join(save_path, "Blend_My_NFTs Output", "NFT_Data")
        batch_json_save_path = os.path.join(Blend_My_NFTs_Output, "Batch_Data")
        nftBatch_save_path = os.path.join(save_path, "Blend_My_NFTs Output", "Generated NFT Batches")

        fail_state, failed_batch, failed_dna, failed_dna_index = Checks.check_FailedBatches(batch_json_save_path)

        if fail_state:
            row = layout.row()
            self.layout.operator("exporter.nfts", icon='RENDER_RESULT', text="Generate NFTs & Create Metadata")

            row = layout.row()
            row.alert = True
            row.operator("exporter.resume_nfts", icon='ERROR', text="Resume Failed Batch")

        if not fail_state:
            row = layout.row()
            self.layout.operator("exporter.nfts", icon='RENDER_RESULT', text="Generate NFTs & Create Metadata")


class BMNFTS_PT_Refactor(bpy.types.Panel):
    bl_label = "Refactor Batches"
    bl_idname = "BMNFTS_PT_Refactor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blend_My_NFTs'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_scene = scene.input_tool

        row = layout.row()
        layout.label(text="Ensure all batches have been created before refactoring.")
        layout.label(text="Refactoring combines all batches into one easy to manage folder.")


        row = layout.row()
        self.layout.operator("refactor.batches", icon='FOLDER_REDIRECT', text="Refactor Batches")


class BMNFTS_PT_Other(bpy.types.Panel):
    bl_label = "Other"
    bl_idname = "BMNFTS_PT_Other"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blend_My_NFTs'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_scene = scene.input_tool

        """
        Export Settings:
        This panel gives the user the option to export all settings from the Blend_My_NFTs addon into a config file. Settings 
        will be read from the config file when running heedlessly.
        """
        layout.label(text=f"Running Blend_My_NFTs Headless:")

        save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)

        if save_path and os.path.isdir(save_path):
            row = layout.row()
            self.layout.operator("export.settings", icon='FOLDER_REDIRECT', text="Export BMNFTs Settings to a File")
        else:
            row = layout.row()
            layout.label(text=f"**Set a Save Path in Create NFT Data to Export Settings")

        row = layout.row()

        row = layout.row()
        layout.label(text=f"Looking for help?")

        row = layout.row()
        row.operator("wm.url_open", text="Blend_My_NFTs Documentation",
                     icon='URL').url = "https://github.com/torrinworx/Blend_My_NFTs"

        row = layout.row()
        row.operator("wm.url_open", text="YouTube Tutorials",
                     icon='URL').url = "https://www.youtube.com/watch?v=ygKJYz4BjRs&list=PLuVvzaanutXcYtWmPVKu2bx83EYNxLRsX"
        row = layout.row()
        row.operator("wm.url_open", text="Join Our Discord Community!",
                     icon='URL').url = "https://discord.gg/UpZt5Un57t"

        row = layout.row()
        layout.label(text=f"{BMNFTS_VERSION}, {LAST_UPDATED}")


# ======== Blender add-on register/unregister handling ======== #
classes = (
    # Property Group Classes:
    BMNFTS_PGT_Input_Properties,

    # Operator Classes:
    createData,
    exportNFTs,
    resume_failed_batch,
    refactor_Batches,
    export_settings,

    # Panel Classes:
    BMNFTS_PT_CreateData,
    BMNFTS_PT_GenerateNFTs,
    BMNFTS_PT_Refactor,
    BMNFTS_PT_Other,
) + Custom_Metadata_UIList.classes_Custom_Metadata_UIList + Logic_UIList.classes_Logic_UIList


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=BMNFTS_PGT_Input_Properties)

    bpy.types.Scene.custom_metadata_fields = CollectionProperty(type=Custom_Metadata_UIList.CUSTOM_custom_metadata_fields_objectCollection)
    bpy.types.Scene.custom_metadata_fields_index = IntProperty()

    bpy.types.Scene.logic_fields = CollectionProperty(type=Logic_UIList.CUSTOM_logic_objectCollection)
    bpy.types.Scene.logic_fields_index = IntProperty()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.input_tool

    del bpy.types.Scene.custom_metadata_fields
    del bpy.types.Scene.custom_metadata_fields_index

    del bpy.types.Scene.logic_fields
    del bpy.types.Scene.logic_fields_index


if __name__ == '__main__':
    register()
    runAsHeadless()
