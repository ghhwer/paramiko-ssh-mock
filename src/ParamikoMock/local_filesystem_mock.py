"""
This submodule implements the LocalFilesystemMock and LocalFileMock classes.
"""
# SFTPFileSystem is a class that stores the file system for the SFTPClientMock
class LocalFilesystemMock():
    """
    LocalFilesystemMock is a class that stores the mocked local filesystem.
    __This is mainly an internal class and should not be used directly.__
    """
    file_system: dict[str, "LocalFileMock"] = {}

    def add_file(self, path:str, file_mock:"LocalFileMock"):
        self.file_system[path] = file_mock

    def get_file(self, path):
        return self.file_system.get(path)
    
    def remove_file(self, path):
        self.file_system.pop(path, None)

class LocalFileMock():
    """
    This class mocks a file in the local filesystem.
    """
    write_history = []
    file_content = None

    def write(self, data):
        self.write_history.append(data)
        if self.file_content is None:
            self.file_content = data
        else:
            self.file_content += data
