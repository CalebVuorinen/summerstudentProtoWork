from ROOT import TTree, TFile, TH1D, TH2D, TH3D, MethodProxy, gInterpreter
from IPython.display import HTML, Markdown, display
from time import time
from array import array
import ROOT
import sys
from PyTreeReader import PyTreeReader
## TODO - TEntryList for filters
## TODO - New file for mapping and another tree from that
## TODO - New File for flatmapping
## TODO - Fix the TreeReaderValue and type of the function

class tree(object):
    def __init__(self, tree):
        #self.filename = file
        #self.treename = tree
        #self.file = TFile(self.filename)
        #self.tree = self.file.__getattr__(self.treename)
        self.tree = tree
        self.names = [b.GetName() for b in self.tree.GetListOfBranches()]
        self.createPyTreeReader(tree)
        self.filters = []
        self.c_filters = []

        self.cache_c_filters = []
        self.cache_filters = []

        self.maps = []
        self.cache_maps = []
        self.flatMaps = []
        self.cache_flatMaps = []
        self.non_cached_transformations = []
        self.cached_transformations = []

        self.newCacheFilters = False

        self.newCache = False
        self.hvalue = 0
        self.useCache = False
        self.cacheEntryList = []

        self.caching = False
        self.wrappers = {}
        #Uses this for mapping and flatmapping
        self.cachedTree = None
        #self.PyTreeReader = None

    def getEntries(self):
        entries = self.tree.GetEntries()
        print entries

    def head(self, rows = 5):
        reader =  self.PyTreeReader
        names = self.names
        text  = '|' + '|'.join(names) + '|\n'
        text += '|' + '|'.join('---' for n in names) + '|\n'
        i = 0
        if self.useCache:
            print "USES CACHED DATA"
            position = 0
            for entry in reader:
                if self.testEntryList.Contains(position):
                    if self.__apply_filters:
                        if self.__apply_filters(entry) : continue
                        text += '|' + '|'.join(str(entry.__getattr__(n)) for n in names) + '|\n'
                        i += 1
                        if i >= rows : break
                    else:
                        text += '|' + '|'.join(str(entry.__getattr__(n)) for n in names) + '|\n'
                        i += 1
                        if i >= rows : break
                position += 1
        else:
            for entry in reader:
                    if self.__apply_filters(entry) : continue
                    text += '|' + '|'.join(str(entry.__getattr__(n)) for n in names) + '|\n'
                    i += 1
                    if i >= rows : break
        self.__reset_filters()
        display(Markdown(text))

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

        if self.filters or self.cache_filters:
            if self.useCache:
                print "USES CACHED DATA"
                position = 0
                for entry in self.tree:
                    #if self.testEntryList.Contains(position):
                    #if self.__apply_filters(entry) : continue
                    args = [entry.__getattr__(v) for v in vars]
                    self.h.Fill(*args)
                    #position += 1
            else:
                for entry in self.tree:
                    if self.__apply_filters(entry) : continue
                    args = [entry.__getattr__(v) for v in vars]
                    self.h.Fill(*args)
        else:
            print vars
            print self.tree
            print self.h
            self.__fill_histogram(vars, self.tree, self.h)
        self.__reset_filters()
        return self.h

# -- Apply Transformations
    def __apply_filter(self, entry):
        #We need this if we want to use the correct order and apply only 1 filter at a time.
        #What should this return?
        filtered = False
        for func in self.cache_filters:
            if not func(entry) :
                filtered = True
                break
        return filtered

    def __apply_filters(self, entry):
        filtered = False
        for f in self.filters:
            if not f(entry) :
                filtered = True
                break
        return filtered

    def __apply_filters_cache(self, entry):
        filtered = False
        #We have to use normal filters for filtering
        filterlist = self.cache_filters
        for f in filterlist:
            if not f(entry) :
                filtered = True
                break
        return filtered

    #TODO CHECK IF THIS IS DOABLE LIKE THIS!
    def __apply_map(self):
        mapped = False
        maplist = self.maps
        for m in maplist:
            self.tree = map(m, self.tree)
            print self.tree
            # TODO here maybe use friendTree and return that? always create a new friendTree when applying map?
            # If its found then always  rewrite / use it instead of normal self.tree.
            # The functionality of filters has to be changed also

            # We could also first run it so that is changes the self.tree
            # Then step by step implement friendTree because it has to be implemented in many places.

            #if not m(tree):
            mapped = True
            break
        return mapped

    def __apply_map_cached(self, func):
        # Creates a new tree, and applies a new column to that with mapped values.
        # Currently it creates new file (Tree) and adds a new column to it.
        # It calculates the new values but it doesnt fill the branch with it.
        # TODO FIX APPLYING VALUES TO THE BRANCH
        mapped = False
        myvar = array( 'i', [ 0 ] )
        #if self.cachedTree = None:
        events = self.tree.GetEntries()
        newfile = TFile("newMappedFile.root","RECREATE")
        newtree = self.tree.CloneTree(0)
        leafValues = map(func, self.tree)
        #else:
        #    events = self.cachedTree.GetEntries()
        #    newfile = TFile("newMappedFile.root","RECREATE")
        #    newtree = self.cachedTree.CloneTree(0)
        #    leafValues = map(func, self.cachedTree)
        #myvar = array(leafValues)
        listofBranch = newtree.GetListOfBranches()

        #newBranch = newtree.Branch( "new_vars" , leafValues, leaves )
        newBranch = newtree.Branch("mappedVal", myvar, 'mappedVal/I')
        for b in listofBranch:
            print b
        #for i in range(events):
            #self.tree.GetEntry(i)
        for val in leafValues:
            #newtree.Branch('myvar')
            newtree.mappedVal = val
            #print newtree.myvar
            #newtree.getBranch('myvar')
            #fill the new column here with mapped values
            newtree.Fill()
        newtree.Write()
        self.cachedTree = newtree

        print "Saved tree"
        #self.tree.Branch( 'testfirstVar', mystruct, 'testsecondVar' )
        #print maptree
        #self.file = TFile(self.filename)
        #self.tree = self.file.__getattr__(self.treename)
        #mappedTreeFile = TFile(self.filename, 'RECREATE')
        #mappedTree = self.file.__getattr__(self.treename)
        #for val in maptree:
        #    mappedTree.fMyTest = val
        #    mappedTree.Fill()
        #mappedTree.Write()
        #mappedTreeFile.Close()
        mapped = True
        #print mappedTree
        #break
        return mapped

# -- Reset lists for the next run
    def __reset_maps(self):
        self.maps = []
        self.mapvalue = 0
        self.flatMaps = []

    def __reset_filters(self):
        self.filters = []
        self.c_filters = []
        self.cache_c_filters = []
        self.non_cached_transformations = []

# -- You can reset the cache with this command
    def resetcache(self):
        #Reset cache for testing purposes
        self.useCache = False
        self.cache_filters = []
        self.cache_c_filters = []

        self.filters = []
        self.c_filters = []
        self.cacheEntryList = []

        self.hvalue = 0

        self.mapvalue = 0
        self.maps = []
        self.cache_maps = []

        self.flatMaps = []
        self.cache_flatMaps = []

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
        if type(func) is MethodProxy:
            self.c_filters.append(func)
            self.non_cached_transformations.append(func)
        else:
            self.filters.append(func)
            self.non_cached_transformations.append(func)
        return self
        #TODO still have to check the order of the functions that it stays the same when runnign procesesses and checking hash

# -- End of Transformations
    def cache(self):
        reader = self.PyTreeReader
        print self.PyTreeReader
    #Have to compare __code__ functions of the functions
        non_cached_transformationsList = self.non_cached_transformations
        test_cached_filters = [f.__code__ for f in self.cache_filters]
        test_cached_maps = [f.__code__ for f in self.cache_maps]
        test_cached_flatMaps = [f.__code__ for f in self.cache_flatMaps]
        print self.cache_filters
        for typefunc in non_cached_transformationsList:
            print typefunc
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
        print self.filters
        print self.cache_filters
        self.cache_filters = self.filters
        print self.cache_filters
        self.filters = []
        self.cache_maps = self.maps
        self.maps = []
        self.cache_flatMaps = self.flatMaps
        self.flatMaps = []
        self.cached_transformations = non_cached_transformationsList
        self.non_cached_transformations = []
        #Re-run the identified values
        print "new cache ? - %s" %self.newCache
        if self.newCache:
            self.testEntryList.Reset()
            self.cachedTree = None
            test_cached_filters = [f.__code__ for f in self.cache_filters]
            test_cached_maps = [f.__code__ for f in self.cache_maps]
            test_cached_flatMaps = [f.__code__ for f in self.cache_flatMaps]
            position = -1
            #print test_cached_filters
            print "Self.cache_filters"
            print self.cache_filters
            for entry in reader:
                position += 1
                if self.__apply_filter(entry) : continue
                self.testEntryList.Enter(position)
            #for func in self.cached_transformations:
            #    if func.__code__ in test_cached_filters:
            #        #Apply filter, return something?
            #        print "We have a filter"
            #        #TODO THE BUG MIGHT BE HERE TODO
            #        for entry in reader:
            #            position += 1
            #            # TODO how to we use all filters?
            #            if self.__apply_filter(func, entry) : continue
            #            #if testEntryList.Contains(!position):
            #            #print "value : ", position, " ", entry
            #            self.testEntryList.Enter(position)
            #    elif func.__code__ in test_cached_maps:
            #        #Apply map, return something?
            #        print "We have a map"
            #        self.__apply_map_cached(func)
            #    elif func.__code__ in test_cached_flatMaps:
            #        #Apple flatmap, return something?
            #        print "We have a flatmap"
            #    else:
            #        print "Function was not found in the lists"

        #TODO it still needs to actually generate the event cache with the functions
        # We could create a list inside that has the funcs and then it just runs with that one. or just use the same one that we already have?
        self.useCache = True
        self.newCache = False
        return self



    def createPyTreeReader(self, tree):
        #TODO figure out to use this to fill the histogram
        #TODO or should we first do it in UI?
        print "comes here"
        self.testEntryList = ROOT.TEntryList("testEntryList", "TestTitle", tree)
        self.PyTreeReader = PyTreeReader(tree)
        print self.PyTreeReader
        return self

    def changeReaderTree(self,tree):
        self.PyTreeReader.setTree(tree)
        return self

    def readerhisto(self, variables):
        # -- TODO fix the variables and read
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
        print reader
        for v in vars:
            print v
        v = 'recoGenMETs_genMetCaloAndNonPrompt__HLT8E29'
        for entry in reader:
            if self.testEntryList.Contains(position):
                #for v in vars:
                #    print entry.__getattr__(v)
                test1 = getattr(entry, v)
                test2 = getattr(test1(), 'obj')
                test3 = getattr(test2, 'front')
                test4 = getattr(test3(), 'sumet')
                #test1 = [getattr(entry, v) for v in vars] [entry.__getattr__(v) for v in vars]
                #test =
                test = test4
                if(n == 1):
                    self.h.Fill(test)
                elif(n == 2):
                    self.h.Fill(test, test)

                #Add the wanted values into a list and add use them to fill the histo

                #for v in vars:
                #    print "v"
                #    print v
                # test = entry.__getattr__(v)
                #    % (','.join(['*'+v for v in vars]))
                #args = [entry.__getattr__(v) for v in vars]
                #test = entry.v
                #self.h.Fill(*args)

            position += 1
        self.__reset_filters()
        return self.h


    #TODO Uses C++ functions, not implemented yet
    def __fill_histogram(self, vars, tree, h):
        #hvalue = hash(tuple(vars+self.c_filters))
        #self.hvalue = hvalue
        #print hvalue
        #print self.wrappers
        #if hvalue in self.wrappers :
        #     self.wrappers[hvalue](h,tree)
        #     return
        branches = []
        for f in self.c_filters:
            ret,func,args = self.__analyse_signature(f)
            for arg in args : branches.append(tuple(arg.split()))

        #-- Get the branches to be histogramed.
        #-- TODO: We need to get the proper types
        #-- TODO: We need to be able to read layers from trees to get all the entries
        #-- TODO: We could used the PyTreeReader here.
        #-- TODO: Figure out if we want to use the loop in UI or keep it behind
        #--       Maybe using a UI to loop would be more effienct because it is more reliable and easier to fix for now

        #-- TODO: Figure out a way of using TEntryList and mapped TTrees inside of JIT code

        for v in vars:
            branches.append(('int',v))
        branches = list(set(branches)) # remove duplicates
        hname = h.__class__.__name__
        funcname = 'wrapper%d' % int(time())
        wrapper =  'void %s(%s& h, TTree* t) {\n' % (funcname, hname)
        wrapper += '  TTreeReader reader(t);\n'
        for arg in branches :
            atype, aname = arg
            if atype[-1] == '&' : atype = atype[:-1]
            wrapper += '  TTreeReaderValue<%s> %s(reader, "%s");\n' % (atype, aname, aname)
        wrapper += '  while (reader.Next()) {\n'
        for f in self.c_filters:
            ret,func,args = self.__analyse_signature(f)
            wrapper += '    if( ! %s(%s) ) continue;\n' % (func,','.join(['*'+a.split()[1] for a in args]) )
        wrapper += '    h.Fill(%s);\n' % (','.join(['*'+v for v in vars]))
        wrapper += '  }\n'
        wrapper += '}\n'

        #This does print it all, however we should be able to add this into an
        # entryList and then read it with Python when we call it next time
        print wrapper
        gInterpreter.Declare(wrapper)
        wfunc = ROOT.__getattr__(funcname)
        if self.useCache:
            self.wrappers[hvalue] = wfunc
            self.useCache = False
        self.test =  wfunc(h,tree)
        wfunc(h,tree)
        return self



    def __analyse_signature(self, f):
        signature = f.__doc__
        m = re.search('(.*)[ ]+(.*)\((.*)\).*', signature)
        return m.group(1), m.group(2), tuple(m.group(3).split(','))
