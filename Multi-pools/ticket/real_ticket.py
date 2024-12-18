"""
AWS GameLift Matchmaking Ticket Handler
AWS GameLift 匹配票据处理系统

This module implements a real-time matchmaking ticket system for AWS GameLift, supporting multiple game modes
and flexible player configurations.
本模块实现了一个AWS GameLift实时匹配票据系统，支持多种游戏模式和灵活的玩家配置。

Key features 主要特性:
- Supports multiple game modes (支持多种游戏模式): Classic经典, Practice练习, Survival生存
- Handles dynamic player grouping with configurable team sizes (处理动态玩家分组，可配置队伍大小)
- Implements matchmaking monitoring with real-time status updates (实现实时状态更新的匹配监控)
- Manages player attributes including skill ratings and latency (管理玩家属性，包括技能评级和延迟)
- Provides detailed matchmaking statistics and logging (提供详细的匹配统计和日志记录)

Main Components 主要组件:
- RealTicket: Core class managing matchmaking tickets and player groups
  核心类，管理匹配票据和玩家组
- Player Generation: Creates mock players with realistic skill distributions
  玩家生成：创建具有真实技能分布的模拟玩家
- Monitoring System: Tracks ticket status and completion rates
  监控系统：跟踪票据状态和完成率
- Batch Processing: Handles player groups in configurable batch sizes
  批处理：以可配置的批次大小处理玩家组

Dependencies 依赖: boto3, numpy, datetime, threading
"""

from datetime import datetime

import json, os, random, time
import string
import uuid
import boto3
import numpy as np
import threading


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def split_array(arr, team_size):
    # print(f"split_array: {team_size}")
    if len(arr) <= 4:
        return [arr]
    result = []
    i = 0
    while i < len(arr):
        sub_len = random.randint(1, team_size)
        sub_len = min(sub_len, len(arr) - i)
        result.append(arr[i:i+sub_len])
        i += sub_len
    return result

def format_elapsed_time(seconds):
  hours = seconds // 3600
  minutes = (seconds % 3600) // 60
  seconds = seconds % 60
  if hours > 0:
      return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
  return f"{minutes:02d}:{seconds:02d}"

def calculate_elapsed_time(start_time, end_time):
  # Convert to datetime if they're strings
  if isinstance(start_time, str):
    start_time = datetime.fromisoformat(start_time)
  if isinstance(end_time, str):
    end_time = datetime.fromisoformat(end_time)
  
  # Calculate the time difference
  elapsed = end_time - start_time
  # Get elapsed time in different units
  return elapsed.total_seconds()

def generate_scores(num_players, median=1000, std_dev=400):
    scores = np.random.normal(loc=median, scale=std_dev, size=num_players)
    scores = [max(1, int(score)) for score in scores]
    return scores

# gamelift = boto3.client('gamelift', region_name='us-east-1')
ALL_GAMEMODES = [ "Classic", "Practice", "Survival" ]
MAX_TEAM_SIZE = 5
MAX_TEAM_SIZE_SAMLL = 2
LATENCY_MEDIAN = 70

class RealTicket():

  def __init__(self, name):
    self.players = []
    self.ticketIds = []
    self.completeTickets = []
    self.failedTickets = []
    self.machmakingConfigurationName = name
    self.start_time = None
    self.end_time = None
    pass

  def call(self):
    print("RealTicket")

  def monitorTicket(self, logfilePath):
    try:
      while True:
        print(self.ticketIds)
        for ticketId in self.ticketIds:
          response = self.gamelift.describe_matchmaking(TicketIds=[ticketId])
          for ticket in response['TicketList']:
            # print(ticket)
            if ticket['Status'] == 'COMPLETED':
              elaspdTime = calculate_elapsed_time(ticket['StartTime'], ticket['EndTime'])
              self.ticketIds.remove(ticketId)
              self.completeTickets.append(elaspdTime)
              print(f"{ticket['ConfigurationName']} - {ticketId} - {ticket['Status']} - {elaspdTime}")
              print(f"{ticket}")
            elif  ticket['Status'] == 'CANCELLED' or ticket['Status'] == 'FAILED' or ticket['Status'] == 'TIMED_OUT':
              elaspdTime = calculate_elapsed_time(ticket['StartTime'], ticket['EndTime'])
              self.ticketIds.remove(ticketId)
              self.failedTickets.append(elaspdTime)
              print(f"{ticket['ConfigurationName']} - {ticketId} - {ticket['Status']} - {elaspdTime}")
            else:
              print(f"{ticket['ConfigurationName']} - {ticketId} - {ticket['Status']} - {len(ticket['Players'])} - {ticket['StartTime']}")
        
        if self.end_time is not None and len(self.ticketIds) == 0:
          complete_avg = sum(self.completeTickets) / len(self.completeTickets) if self.completeTickets else 0
          failed_avg = sum(self.failedTickets) / len(self.failedTickets) if self.failedTickets else 0

          print(logfilePath)
          with open(logfilePath, 'a') as outputfile:
            print(f"\n\nMatchmaking Monitor for [{self.machmakingConfigurationName}] Done!", file=outputfile)
            print(f"Complete Tickets: {len(self.completeTickets)}, Average Time: {complete_avg:.2f} seconds", file=outputfile)
            print(f"Failed Tickets: {len(self.failedTickets)}, Average Time: {failed_avg:.2f} seconds", file=outputfile)
          break
        time.sleep(3)
    except Exception as e:
      print(f"Error during monitoring: {e}")
    pass

  def mockPlayer(self, mrr_vals, lty_vals):
    playerId = "player-" + str(random.randint(1000000, 9999999))
    skill_mrr = random.sample(mrr_vals, 1)[0]
    latency = random.sample(lty_vals, 1)[0]
    player = {
        'PlayerId': playerId,
        'PlayerAttributes': {
            'skill': {
              'N': skill_mrr
            }
        },
        "LatencyInMs":{
          "us-east-1": latency
        }
    }
    return player

  def mockPlayers(self, num_players):
    mrr_vals = generate_scores(num_players, 1000, 200)
    lty_vals = generate_scores(num_players, LATENCY_MEDIAN, 20)

    for i in range(num_players):
      self.players.append(self.mockPlayer(mrr_vals, lty_vals))
    pass

  def startMatchmaking(self, gamelift, num_players, ticketPrefix, logs):
    self.gamelift = gamelift
    self.mockPlayers(num_players)
    sub_players = split_array(self.players, MAX_TEAM_SIZE)
    if "All" in self.machmakingConfigurationName:
      pass
    elif "Classic" in self.machmakingConfigurationName:
      pass
    elif "Practise" in self.machmakingConfigurationName:
      pass
    elif "Survival" in self.machmakingConfigurationName:
      sub_players = split_array(self.players, MAX_TEAM_SIZE_SAMLL)
      pass
    else:
      pass   
    
    total_batches = len(sub_players)

    print(f"\nStarting matchmaking for {self.machmakingConfigurationName}")
    print(f"Total players: {num_players}, Batches: {total_batches}")

    # monitor the tickets
    logfilePath = f"{os.getcwd()}/{logs}"
    monitor_thread = threading.Thread(target=self.monitorTicket, args=(logfilePath,))
    monitor_thread.start()

    self.start_time = datetime.now()
    try:
      for index, batch_players in enumerate(sub_players, 1):
        progress = (index / total_batches) * 100
        print(f"==== Progress: {progress:.1f}% - Batch {index}/{total_batches} - "
              f"==== Processing {len(batch_players)} players in {self.machmakingConfigurationName}")
        
        sleepRandomTimeLower = 1
        sleepRandomTimeUpper = 3
        gameModes = []
        if "All" in self.machmakingConfigurationName:
          randomSize = random.randint(1, len(ALL_GAMEMODES))
          gameModes = random.sample(ALL_GAMEMODES, randomSize)
        elif "Classic" in self.machmakingConfigurationName:
          gameModes = ["Classic"]
          sleepRandomTimeLower = 2
          sleepRandomTimeUpper = 6
          pass
        elif "Practice" in self.machmakingConfigurationName:
          gameModes = ["Practice"]
          sleepRandomTimeLower = 2
          sleepRandomTimeUpper = 6
          pass
        elif "Survival" in self.machmakingConfigurationName:
          gameModes = ["Survival"]
          sleepRandomTimeLower = 2
          sleepRandomTimeUpper = 6  
          pass
        else:
          gameModes = ALL_GAMEMODES
          pass

        for batch_player in batch_players:
          batch_player['PlayerAttributes']['GameMode'] = {'SL' : gameModes}
        
        print(f"starting matchmaking for: {self.machmakingConfigurationName} with players: {len(batch_players)} game mode: {gameModes}")
        # print(f"{json.dumps(batch_players, indent=2)}")
        response = self.gamelift.start_matchmaking(
          TicketId= ticketPrefix + generate_random_string(10),
          ConfigurationName=self.machmakingConfigurationName,
          Players=batch_players
        )

        ticketId = response['MatchmakingTicket']['TicketId']
        self.ticketIds.append(ticketId)
        time.sleep(random.randint(sleepRandomTimeLower, sleepRandomTimeUpper))
  
    except Exception as e:
      print(f"\nError during matchmaking: {str(e)}")
    finally:
      self.end_time = datetime.now()
      monitor_thread.join()  # Wait for monitor thread to complete
      total_time = (self.end_time - self.start_time).total_seconds()
      formatted_time = format_elapsed_time(int(total_time))

      print(f"\n\nMatchmaking Summary for {self.machmakingConfigurationName}")
      print(f"Total Players: {num_players}")
      print(f"Total Batches: {total_batches}")
      print(f"Total Time: {formatted_time}")
      print(f"Average Time per Batch: {(total_time/total_batches):.2f} seconds")
