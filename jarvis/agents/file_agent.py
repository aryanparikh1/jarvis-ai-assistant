"""File Agent — delegates to file_tools."""
from jarvis.tools.file_tools import read_file, write_file, delete_file, search_files, list_directory
from jarvis.utils.logger import logger

class FileAgent:
    def read(self, path): return read_file(path)
    def write(self, path, content): return write_file(path, content)
    def delete(self, path): return delete_file(path)
    def search(self, query, directory="~"): return search_files(query, directory)
    def list(self, path="."): return list_directory(path)

file_agent = FileAgent()
