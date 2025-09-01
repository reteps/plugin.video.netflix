# NFSessionOperations
import resources.lib.run_service as run_service
from resources.lib.services.nfsession.nfsession import NetflixSession
from resources.lib.globals import G
import sys
from dotenv import load_dotenv
if __name__ == "__main__":
    load_dotenv()
    G.init_globals(sys.argv)
    session = NetflixSession()
    session.nfsession.login()
    session.nfsession.fetch_initial_page()
    # NFSessionOperations.fetch_initial_page()
