import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import requests
import json
from pprint import pprint

load_dotenv('token.env')
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='?')

@bot.command(name='dict')
async def get_definition(ctx, message):
    app_id = '68f523a4'
    app_key = 'cc0f437b7719d43782471e128e686635'
    language = 'en-gb'
    word_id = message
    url = f'https://od-api.oxforddictionaries.com/api/v2/entries/{language}/{word_id.lower()}?fields=definitions&strictMatch=false'
    
    r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})

    # testing = f'https://od-api.oxforddictionaries.com:443/api/v2/entries/{language}/test'
    # test_r = requests.get(testing, headers={'app_id': app_id, 'app_key': app_key})
    # test_data = json.loads(test_r.text)

    # for i in test_data['results']:
    #     for x in i['lexicalEntries']:
    #         for j in x['entries']:
    #             for h in j['senses']:
    #                 for y in h['definitions']:
    #                     print(type(y))

    data = json.loads(r.text)
    definitions = []
    pprint(data)

    # for i in data['results']:
    #     for x in i['lexicalEntries']:
    #         for j in x['entries']:
    #             for h in j['senses']:
    #                 for y in h['definitions']:
    #                     print(type(y))
    #                     definitions.append(y.capitalize())

    # response = f'**{word_id.capitalize()}** definitions:\n* {build_response(definitions)}' 
    # await ctx.send(response)

def build_response(res):
    return "\n* ".join(res)

client =  discord.Client()
bot.run(TOKEN)