import hou
def run():
    selectedNodes = hou.selectedNodes()    
    parent = selectedNodes[0].parent()    

    for node in selectedNodes:
        # Create Subnet              
        subnet = parent.createNode("subnet",node_name="CloneSubnet")
        subnet.setPosition(node.position()+hou.Vector2(-2,0))        

        # Get the parameter layout and the parameters of the OTL
        otlParmTemplateAsCode = node.parmTemplateGroup().asCode()
        otlParmTemplateAsCode = otlParmTemplateAsCode.replace(", ,", ',')
        # otlParmTemplateAsCode = otlParmTemplateAsCode.replace('default_expression_language=hou.scriptLanguage.Hscripticon_names=([]),', '')       
    
        exec_ns = {'hou': hou}
        exec(otlParmTemplateAsCode, exec_ns)
        subnet.setParmTemplateGroup(exec_ns['hou_parm_template_group'])

        nodeAsCode = node.asCode()            

        # Swap node name & type to subnet's
        nodeAsCode = nodeAsCode.replace(node.name(),subnet.name())
        nodeAsCode = nodeAsCode.replace(node.type().name(),subnet.type().name())
        
        # Remove Node Creation Part
        nodeAsCodeList = nodeAsCode.split('\n\n')
        nodeAsCodeList.pop(1)
        nodeAsCode = '\n\n'.join(nodeAsCodeList)                
        
        exec_ns = {'hou': hou}
        exec(nodeAsCode, exec_ns)

        # move the "Standard" folder below the "Spare" folder in the parmTemplate of subnet
        parmTemplateGroup = subnet.parmTemplateGroup()
        standardFolder = parmTemplateGroup.findFolder("Standard")
        if standardFolder:
            parmTemplateGroup.remove(standardFolder)
            # re-fetch spareFolder: prior copies are invalidated after mutating the group
            spareFolder = parmTemplateGroup.findFolder("Spare")
            if spareFolder:
                parmTemplateGroup.insertAfter(spareFolder, standardFolder)
            else:
                parmTemplateGroup.append(standardFolder)
            subnet.setParmTemplateGroup(parmTemplateGroup)         
        
        # rename node
        subnet.setName(node.name(), unique_name=True)

        # set input labels
        if node.childTypeCategory().name() == 'Sop':

            labels = node.inputLabels()
            for i in range(min(len(labels),4)):
                label_parm = subnet.parm('label'+str(i+1))
                label_parm.set(labels[i])

            # fix item input positions. this doesnt work properly, need to store offset and fix after paste.
            for idx, item in enumerate(node.items(['1', '2', '3', '4'])):
                if item is None:
                    continue
                subnet_item = subnet.item(str(idx+1))
                if subnet_item:
                    subnet_item.setPosition(item.position())



        # set COP inputs
        if node.childTypeCategory().name() == 'Cop':
            subnet.deleteItems(subnet.children())
            subnet.setCompressFlag( node.isCompressFlagSet())
            inputLabels = node.inputLabels()
            outputLabels = node.outputLabels()
            # inputTypes = node.inputDataTypes()

            subnet.parm('inputs').set(len(inputLabels))
            subnet.parm('outputs').set(len(outputLabels))

            # maybe ensure input is atleast 1 so this parm exists
            menu = subnet.parm("inputtype1").menuContents()
            #('int', 'ID', 'float', 'Mono', 'vector2', 'UV', 'vector', 'RGB', 'vector4', 'RGBA', 'geo', 'Geometry', 'ivdb', 'Integer VDB', 'fvdb', 'Float VDB', 'vvdb', 'Vector VDB', 'cable', 'Cable')
            

            for idx, input in enumerate(node.inputDataTypes()):                
                dtype = menu[ menu.index(input)-1 ]
                subnet.parm("inputlabel"+str(idx+1)).set(inputLabels[idx])
                subnet.parm("inputtype"+str(idx+1)).set(dtype)

            for idx, output in enumerate(node.outputDataTypes()):
                dtype = menu[ menu.index(output)-1 ]
                subnet.parm("outputlabel"+str(idx+1)).set(outputLabels[idx])
                subnet.parm("outputtype"+str(idx+1)).set(dtype)
                

            # inputTypes gives the label name such as "Mono" instead of the needed parm value "float"
            # we need to map them, maybe there already exists a function?
            # subnet.

        # everything before this point is just for the subnet and parameters.
        # below we copy the network contents.        
        
        # hou.copyNodesTo(node.children(), subnet)
        # Node.allItems() instead of children() to include network items such as dots and sticky notes
        node.copyItemsToClipboard(node.allItems())
        subnet.pasteItemsFromClipboard()
        
        net_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if net_editor:
            net_editor.setCurrentNode(subnet)
