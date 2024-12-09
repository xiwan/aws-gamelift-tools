import json, os, random
import threading
import boto3
from .real_ticket import RealTicket

class MainTicket():
  def __init__(self):
    self.gamelift = boto3.client('gamelift')
    self.realtickets = []
    self.realtickets.append(RealTicket('Radiant-Dire-All'))
    self.realtickets.append(RealTicket('Radiant-Dire-Survival'))
    self.realtickets.append(RealTicket('Radiant-Dire-Practice'))
    self.realtickets.append(RealTicket('Radiant-Dire-Classic'))
    
    pass

  def call(self):
    RealTicket().call()

  def startMatchmaking(self, gamelift, total_players):
    threads = []
    self.gamelift = gamelift
    # total_players = random.randint(200, 300)
    print(f"total_players: {total_players}")
    for realticket in self.realtickets:
      thread = threading.Thread(target=realticket.startMatchmaking, args=(self.gamelift, total_players,))
      threads.append(thread)
      thread.start()

    # Wait for all threads to complete
    for thread in threads:
      thread.join()

main_ticket = MainTicket()

