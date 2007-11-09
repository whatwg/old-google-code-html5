"""Implementation of DOM 2 treewalker for lxml.etree trees"""
class NodeFilter(object):
    FILTER_ACCEPT = 1
    FILTER_REJECT = 2
    FILTER_SKIP = 3
    
    def acceptNode(self, node):
        raise NotImplementedError

class DOMTreeWalker(object):
    def __init__(self, root, filter):
        self.root = root
        self.currentNode = root
        if hasattr(filter, "acceptNode"):
            self.filter = filter.acceptNode
        else:
            self.filter = filter
    
    def firstChild(self):
        for node in self.currentNode:
            if self.filter(node) == NodeFilter.FILTER_ACCEPT:
                self.currentNode = node
                return node
        return None
    
    def lastChild(self):
        for node in self.currentNode[:][::-1]:
            if self.filter(node) == NodeFilter.FILTER_ACCEPT:
                self.currentNode = node
                return node
        return None
    
    def nextNode(self):
        node = self.currentNode.getnext()
        while node is not None:
            accept = self.filter(node)
            if accept == NodeFilter.FILTER_SKIP:
                node = self._treeOrderNextNode(node, skipChildren=True)
            elif accept == NodeFilter.FILTER_REJECT:
                node = self._treeOrderNextNode(node)
            else:
                break
        
        if node is not None:
            self.currentNode = node
            return node
        else:
            return None
    
    def nextSibling(self):
        node = self.currentNode.getnext()
        while node is not None:
            if self.filter(node) == NodeFilter.FILTER_ACCEPT:
                self.currentNode = node
                return node
            node = node.getnext()
        return None
    
    def parentNode(self):
        node = self.currentNode.getparent()
        while node is not None and self.filter(node) != NodeFilter.FILTER_ACCEPT:
            node = node.getparent()
        if node is not None:
            self.currentNode = node
            return node
        else:
            return None
    
    def previousNode(self):
        #This doesn't handle the case where the current node is changed to a
        #subnode of a skipped node
        node = self._treeOrderPreviousNode(self.currentNode)
        if node is not None:
            self.currentNode = node
            return node
        else:
            return None
    
    def previousSibling(self):
        parent = self.currentNode.getparent()
        idx = parent.getchildren().index(self.currentNode)
        for node in parent[:][idx-1::-1]:
            if self.filter(node) == NodeFilter.FILTER_ACCEPT:
                self.currentNode = node
                return node
        return None
    
    def _treeOrderNextNode(self, node, skipChildren=False):
        if not skipChildren and len(node):
            #If the node has a child node, that is the next node
            return node[0]
        
        #Try the next sibling
        tmp_node = node.getnext()
        if tmp_node is None:
            #There are no siblings so we have to walk up the tree until
            #we find a node with a later sibling or hit the root element
            tmp_node = node
            parent = node.getparent()
            while (parent is not None and
                   len(parent) == parent.getchildren().index(tmp_node)):
                tmp_node = parent
                parent = tmp_node.getparent()
            if len(parent) > parent.getchildren().index(tmp_node):
                #If the node we end up on has a sibling, that is the
                #next node in tree order
                node = tmp_node.getnext()
            else:
                #We must have iterated to the last child of the root
                assert parent == None
                node = None
        return node
    
    def _treeOrderPreviousNode(self, node):
        parent = node.getparent()
        tmp_node = node
        
        #Iterate up the parent chain until we find one that has a previous
        #sibling
        while (parent is not None and
               parent.getchildren().index(tmp_node) == 0):
            tmp_node = parent
            parent = tmp_node.getparent()
        
        if parent is not None and parent.getchildren().index(tmp_node) != 0:
            #If the node we end up on has a previous sibling, the previous node
            #in document order is found at the bottom of the last child chain
            #of that previous sibling
            node = parent[parent.getchildren().index(tmp_node)-1]
            while len(node):
                node = node[-1]
        else:
            #We must have iterated to a child of the root with no previous sibling
            assert parent == None
            node = None
        return node