class JavaCardMethod(object):
    """
    The goal of this class is to make things easier for the JavaCardFrame
    This class would embed the parameters, the bytecode and the exception 
    handlers (more might come later)
    """
    def __init__(self, packageaid, offset):
        """ 
        This object is first created from information of the export_file and 
        the ConstantPool. Those only provide the offset in the Method 
        Component in case of internal references.
        """
        self.packageaid = packageaid
        self.offset = offset

    def feedFromCAP(self, cap_file):
        """ 
        We init it from components of the cap_file
        `offset` is the offset of the class we want to represent in the Method 
        Component as we can find for instance in the ConstantPool.
        """
        # Get the methodInfo is not too complicated
        self.methodinfo = cap_file.Method.methods[self.offset]
        # Now, we also'd like the MethodDescriptorInfo
        self.methoddescriptorinfo = None
        for cls in cap_file.Descriptor.classes:
            for mtd in cls.methods:
                if mtd.method_offset == self.offset:
                    # Bingo !
                    self.methoddescriptorinfo = mtd
                    break
        if self.methoddescriptorinfo is None:
            assert(False, "Method Not found in Descriptor Component")
        # We now care about the exception handlers
        
                
