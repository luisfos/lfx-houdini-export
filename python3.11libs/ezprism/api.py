'''
designed to simplify writing prism tools
'''

def get_prism_projects(core):
    # todo
    # project.name
    # project.path
    pass


class PrismProject():
    def __init__(self, core, project):
        self.core = core
        self.project = project

    def get_shots(self):
        # todo
        pass

    def get_sequences(self):
        # todo
        pass

    def get_assets(self):
        # todo
        pass



    




if __name__ == "__main__":
    import sys
    from pprint import pprint
    sys.path.append("C:/Program Files/Prism2/Scripts")
    # pprint(sys.path)
    import os
    print("PYTHONPATH:", os.environ.get("PYTHONPATH"))

    import PrismCore
    core = PrismCore.create(prismArgs=["noUI"])

    # find list of projects in Prism core
    projects = core.projects
    pprint(dir(projects))

    # use this if you want to load the previously active project
    # core = PrismCore.create(prismArgs=["noUI", "loadProject"])

    print(core.version)