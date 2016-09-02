from ROOT import TTree, TFile, TH1D, TH2D, TH3D, MethodProxy, gInterpreter
from IPython.display import HTML, Markdown, display
import ROOT
from PyTreeReader import PyTreeReader

## TODO - New file for mapping and another tree from that
## TODO - New File for flatmapping
## TODO - Transformations: Map, flatmap

class DataFrame(object):
    def __init__(self, tree):
        self.tree = tree
        self.names = [b.GetName() for b in self.tree.GetListOfBranches()]
        self.createPyTreeReader(tree)
        self.filters = []
        self.cache_filters = []

        self.maps = []
        self.cache_maps = []
        self.flatMaps = []
        self.cache_flatMaps = []
        self.non_cached_transformations = []
        self.cached_transformations = []

        self.newCacheFilters = False

        self.newCache = False
        self.useCache = False
        #Uses this for mapping and flatmapping
        self.cachedTree = None

    def head(self, rows = 5):
        reader =  self.PyTreeReader
        names = self.names
        text  = '|' + '|'.join(names) + '|\n'
        text += '|' + '|'.join('---' for n in names) + '|\n'
        i = 0
        non_cached_transformationsList = self.non_cached_transformations
        test_filters = [f.__code__ for f in self.filters]
        test_maps = [f.__code__ for f in self.maps]
        test_flatMaps = [f.__code__ for f in self.flatMaps]
        if self.useCache:
            position = 0
            for entry in reader:
                if self.testEntryList.Contains(position):
                    if non_cached_transformationsList:
                        for typefunc in non_cached_transformationsList:
                            if typefunc.__code__ in test_filters:
                                if self.__apply_filter(typefunc, entry) :
                                    text += '|' + '|'.join(str(getattr(entry, n)()) for n in names) + '|\n'
                                    i += 1
                                    if i >= rows : break
                    else:
                        text += '|' + '|'.join(str(getattr(entry, n)()) for n in names) + '|\n'
                        i += 1
                        if i >= rows : break
                position += 1
        else:
            position = 0
            filledhead = False
            self.testEntryList.Reset()
            if non_cached_transformationsList:
                for entry in reader:
                    for typefunc in non_cached_transformationsList:
                        if typefunc.__code__ in test_filters:
                            if self.__apply_filter(typefunc, entry):
                                if not self.testEntryList.Contains(position):
                                    self.testEntryList.Enter(position)
                                elif self.testEntryList.Contains(position):
                                    self.testEntryList.Remove(position)
                    position += 1
            else:
                for entry in reader:
                    text += '|' + '|'.join(str(getattr(entry, n)()) for n in names) + '|\n'
                    i += 1
                    filledhead = True
                    if i >= rows : break
                position += 1
            if not filledhead:
                position = 1
                i = 0
                for entry in reader:
                    if self.testEntryList.Contains(position):
                        text += '|' + '|'.join(str(getattr(entry, n)()) for n in names) + '|\n'
                        i += 1
                        if i >= rows : break
                    position += 1
        self.__reset_filters()
        display(Markdown(text))

# -- Apply Transformations
    def __apply_filter(self, func, entry):
        filtered = False
        if func(entry) :
            filtered = True
        return filtered

    def __apply_filters(self, entry):
        filtered = False
        for f in self.filters:
            if not f(entry) :
                filtered = True
                break
        return filtered

    #TODO MAP FUNCTIONALITIES ARE JUST A SKELETONS AND ARE NOT SUPPORTED YET
    def __apply_map(self):
        maplist = self.maps
        for m in maplist:
            self.tree = map(m, self.tree)
            print self.tree
        return self.tree

# -- Reset lists for the next run
    def __reset_maps(self):
        self.maps = []
        self.flatMaps = []

    def __reset_filters(self):
        self.filters = []
        self.non_cached_transformations = []

# -- You can reset the cache with this command
    def resetcache(self):
        #Reset cache for testing purposes
        self.useCache = False
        self.filters = []
        self.cache_filters = []

        self.maps = []
        self.cache_maps = []

        self.flatMaps = []
        self.cache_flatMaps = []

        self.testEntryList.Reset()

        return self

# -- Transformations functions add the functions to list
    def flatMap(self, func):
        self.flatMaps.append(func)
        self.non_cached_transformations.append(func)
        return self

    def map(self, func):
        self.maps.append(func)
        self.non_cached_transformations.append(func)
        return self

    def filter(self, func):
        self.filters.append(func)
        self.non_cached_transformations.append(func)
        return self

# -- End of Transformations
    def cache(self):
        reader = self.PyTreeReader
        #Have to compare __code__ functions of the functions for identification
        non_cached_transformationsList = self.non_cached_transformations
        test_cached_filters = [f.__code__ for f in self.cache_filters]
        test_cached_maps = [f.__code__ for f in self.cache_maps]
        test_cached_flatMaps = [f.__code__ for f in self.cache_flatMaps]
        if len(non_cached_transformationsList) is not len(self.cached_transformations):
            self.newCache = True
        for typefunc in non_cached_transformationsList:
            #Checks if the function is a filter func and if its cached or not.
            if typefunc in self.filters:
                if typefunc.__code__ in test_cached_filters:
                    print "Cached FILTER"
                else:
                    print "NOT cached FILTER"
                    self.newCache = True
            #Checks if the function is a map func and if its cached or not.
            elif typefunc in self.maps:
                if typefunc.__code__ in test_cached_maps:
                    print "Cached MAP"
                else:
                    print "NOT cached MAP"
                    self.newCache = True
            #Checks if the function is a flatMap func and if its cached or not.
            elif typefunc in self.flatMaps:
                if typefunc.__code__ in test_cached_flatMaps:
                    print "Cached flatMap"
                else:
                    print "NOT cached flatMap"
                    self.newCache = True
            else:
                print "ERROR - Function was not found in any of the lists"
        self.cache_filters = self.filters
        self.filters = []
        self.cache_maps = self.maps
        self.maps = []
        self.cache_flatMaps = self.flatMaps
        self.flatMaps = []
        self.cached_transformations = non_cached_transformationsList
        self.non_cached_transformations = []
        #Re-run the identified values
        print "new cache = %s" %self.newCache
        if self.newCache:
            self.testEntryList.Reset()
            #Resets the mapped tree
            self.cachedTree = None
            test_cached_filters = [f.__code__ for f in self.cache_filters]
            test_cached_maps = [f.__code__ for f in self.cache_maps]
            test_cached_flatMaps = [f.__code__ for f in self.cache_flatMaps]
            position = 0
            for entry in reader:
                for typefunc in self.cached_transformations:
                    if typefunc.__code__ in test_cached_filters:
                        if self.__apply_filter(typefunc, entry):
                            if not self.testEntryList.Contains(position):
                                self.testEntryList.Enter(position)
                            elif self.testEntryList.Contains(position):
                                self.testEntryList.Remove(position)
                position += 1
                        # TODO same idea has to be implemented to map and flatmap
        self.useCache = True
        self.newCache = False
        return self

    def createPyTreeReader(self, tree):
        print "Creating the PyTreeReader"
        #TODO Is this the best place for creating the entryList?
        #TODO - Naming of the entrylist?
        self.testEntryList = ROOT.TEntryList("EntryList", "Title", tree)
        self.PyTreeReader = PyTreeReader(tree)
        return self

    def histo(self, variables):
        vars = variables.split(':')
        n = len(vars)
        if(n == 1):
            self.h = TH1D('h',variables, 100,0,0)
        elif(n == 2):
            self.h = TH2D('h',variables, 100,0,0,100,0,0)
        elif(n == 3):
            self.h = TH3D('h',variables)
        else:
            raise Exception('Invalid number of varibales to histogram')
        position = 0
        reader = self.PyTreeReader

        # - With this we will see if there are any functions after the Cache()
        non_cached_transformationsList = self.non_cached_transformations
        test_filters = [f.__code__ for f in self.filters]
        test_maps = [f.__code__ for f in self.maps]
        test_flatMaps = [f.__code__ for f in self.flatMaps]

        #TODO what if testEntryList is empty?
        # - For complex trees this might not work, they might have "layered structures"
        for entry in reader:
            if self.testEntryList.Contains(position):
                if non_cached_transformationsList:
                    for typefunc in non_cached_transformationsList:
                        if typefunc.__code__ in test_filters:
                            if self.__apply_filter(typefunc, entry) :
                                args = [getattr(entry, v)() for v in vars]
                                self.h.Fill(*args)
                            #Do filter
                        elif typefunc.__code__ in test_maps:
                            #Do map
                            print "adding map"
                        elif typefunc.__code__ in test_flatMaps:
                            #Do flatmapping
                            print "adding flatmap"
                        #Here we will identify the function and act accordingly
                else:
                    args = [getattr(entry, v)() for v in vars]
                    self.h.Fill(*args)
            position += 1
        self.__reset_filters()
        return self.h
