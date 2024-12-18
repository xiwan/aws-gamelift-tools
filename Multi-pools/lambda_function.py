# This code implements an AWS Lambda handler that manages GameLift FlexMatch configurations:
# 1. Reads JSON ruleset files for matchmaking configurations
# 2. Updates GameLift FlexMatch configurations with new rulesets:
#    - Generates a random suffix for the ruleset name
#    - Reads ruleset JSON from a config file
#    - Gets current ruleset for the matchmaking config
#    - Deletes the old ruleset
#    - Creates new ruleset with random suffix
#    - Updates matchmaking config to use new ruleset
# 3. If no context provided, starts matchmaking with specified total players
# 4. Returns 200 status code response

import json, os, time, random
import boto3

from ticket import main_ticket

def read_json_file(file_path):
  try:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Ruleset file not found: {file_path}")
            
    with open(file_path, 'r', encoding='utf-8') as file:
      return json.load(file)
  except FileNotFoundError:
    print(f"文件 '{file_path}' 不存在")
  except json.JSONDecodeError:
    print(f"文件 '{file_path}' 不是有效的 JSON 文件")
  except Exception as e:
    print(f"发生错误: {e}")
  return None

def lambda_handler(event, context):

    gamelift = boto3.client('gamelift', region_name=context['aws']['region'])

    if event is None:
        if not context.get('flexmatch') or not context['flexmatch'].get('configurations'):
            print("Missing required flexmatch configurations in context")
            raise ValueError("Invalid context structure")
    
        surfix = random.randint(1,100)
        for config in context['flexmatch']['configurations']:
            # Validate required configuration parameters
            if not config.get('ruleset') or not config.get('name'):
                print(f"Missing required parameters in config: {config}")
                continue

            current_ruleset = ""
            try:
                rulesetName = f"{config['ruleset']}-{surfix}"
                rulesetJson = read_json_file(os.getcwd()+f"/Multi-pools/Configs/{config['ruleset']}.json")

                response = gamelift.describe_matchmaking_configurations(Names=[config['name']])
                current_ruleset = response['Configurations'][0]['RuleSetName']
                print(f"Current ruleset for {config['name']}: {current_ruleset}")

                gamelift.create_matchmaking_rule_set(
                    Name=rulesetName,
                    RuleSetBody=json.dumps(rulesetJson)
                )
                print(f"Created new ruleset: {rulesetName}")

                if config['acceptance'] > 0:
                    gamelift.update_matchmaking_configuration(
                        Name=config['name'],
                        FlexMatchMode='STANDALONE',
                        AcceptanceTimeoutSeconds=config['acceptance'],
                        AcceptanceRequired=True,
                        RuleSetName=rulesetName
                    )
                else:
                    gamelift.update_matchmaking_configuration(
                        Name=config['name'],
                        FlexMatchMode='STANDALONE',
                        AcceptanceRequired=False,
                        RuleSetName=rulesetName
                    )
                print(f"Updated matchmaking configuration: {config['name']} with new ruleset: {rulesetName}")

            except Exception as e:
                print(f"Error during monitoring: {e}")
                pass

            finally:
                gamelift.delete_matchmaking_rule_set(Name=current_ruleset)
                print(f"Removed {current_ruleset}")
                pass

    else:
        for config in context['flexmatch']['configurations']:
           main_ticket.loadMatchMaking(config['name'])

        main_ticket.startMatchmaking(gamelift, context['benchmark'])

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
