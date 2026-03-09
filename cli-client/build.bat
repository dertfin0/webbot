pip install -r requirements.txt
pyinstaller ^
--hidden-import textual ^
--hidden-import python-dotenv --collect-submodules dotenv ^
--hidden-import httpx ^
--onefile ^
--noupx ^
--icon icon.ico ^
main.py