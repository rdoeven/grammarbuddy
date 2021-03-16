import discord
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import textdistance
import re
from collections import Counter
import os

load_dotenv()
TOKEN = os.getenv('TOKEN')
PLAYER_ID = os.getenv("ID")

class grammer_buddy(discord.Client):
    
    def __init__(self):
        super().__init__()
        self.V, self.probs, self.word_freq_dict = self.update_frames()
        self.correcting = False
        self.intake = False

    
    @staticmethod
    def update_frames():
        words = []

        with open('words.txt', 'r') as f:
            file_name_data = f.read()
            file_name_data=file_name_data.lower()
            words = re.findall('\w+',file_name_data)

        V = set(words)

        word_freq_dict = {}  
        word_freq_dict = Counter(words)

        probs = {} 
        Total = sum(word_freq_dict.values())
            
        for k in word_freq_dict.keys():
            probs[k] = word_freq_dict[k]/Total
        
        return V, probs, word_freq_dict

    @staticmethod
    def update_file(bad, correction, delete=False):
        with open('words.txt', "r") as infile:
            data = infile.read()
            data=data.lower()
            words = re.findall('\w+',data)

        with open('words.txt', "w") as outfile:
            for word in words:
                if word != bad:
                    outfile.write("\n" + word)

        with open('words.txt', "a") as afile:
            afile.write(" " + correction)
            if not delete:
                afile.write(" " + bad)
    
    @staticmethod
    def add_to_file(text):
        with open('words.txt', "a") as afile:
            words = re.findall('\w+',text)
            for word in words:
                afile.write(" " + word)

    def my_autocorrect(self, input_word):
        if input_word.lower() in self.V:
            return(input_word)
        else:
            input_word = input_word.lower()
            similarities = [1-(textdistance.Jaccard(qval=2).distance(v,input_word)) for v in self.word_freq_dict.keys()]
            df = pd.DataFrame.from_dict(self.probs, orient='index').reset_index()
            df = df.rename(columns={'index':'Word', 0:'Prob'})
            df['Similarity'] = similarities
            output = df.sort_values(['Similarity', 'Prob'], ascending=False).head()
            return(output.iloc[0]["Word"])
        
    def update_vars(self):
        self.V, self.probs, self.word_freq_dict = self.update_frames()


    async def on_message(self,message):
        if message.author == self.user:
            return

        if message.author.id == int(PLAYER_ID) and not message.content.startswith('$'):
            if self.intake:
                self.add_to_file(message.content)
            elif self.correcting:
                msg = " ".join([self.my_autocorrect(i) for i in message.content.split(" ")])
                if msg.lower() != message.content.lower():
                    await message.channel.send("Wat robbe eigenlijk wil zeggen is: " + msg)
        
        if message.content.startswith("$"):
            if message.content == "$on":
                self.correcting = True
                await message.channel.send("autocorrect turned on")
            
            elif message.content == "$off":
                self.correcting = False
                await message.channel.send("autocorrect turned off")
            
            elif message.content == "$intake on":
                self.intake = True
                await message.channel.send("message intake turned on")
            
            elif message.content == "$intake off":
                self.intake = False
                await message.channel.send("message intake turned off")
            
            elif message.content.startswith("$correct"):
                _, bad, correction = message.content.split(" ")
                self.update_file(bad, correction)
                await message.channel.send(f"correction done, thanks @{message.author}")
            
            elif message.content.startswith("$replace"):
                _, bad, correction = message.content.split(" ")
                self.update_file(bad, correction, True)
                await message.channel.send(f"correction done, thanks @{message.author}")
            
            elif message.content.startswith("$rebuild"):
                self.update_vars()
                await message.channel.send("rebuilded")
            
            elif message.content.startswith("$help"):
                embed=discord.Embed(title="grammarbuddy - Help", description="command [ variable ] - description", color=0xd92f3a)
                embed.add_field(name="$help", value="help function", inline=False)
                embed.add_field(name="$rebuild", value="force update the dictionary", inline=False)
                embed.add_field(name="correct [ mistake ] [ correction ]", value="the mistake is a valid word but used in the wrong context. this command will boost the correction in the dictionary and lower the dictionary rate of the mistake", inline=False)
                embed.add_field(name="replace [ mistake ] [ correction ]", value="the mistake is not even a valid word and used in the wrong context. this command deletes the mistake from the disctionary and boosts the correction", inline=False)
                embed.add_field(name="$intake off", value="stop adding messages to the dictionary", inline=False)
                embed.add_field(name="$intake on", value="start adding messages to the dictionary", inline=False)
                embed.add_field(name="$on", value="turn on autocorrect", inline=False)
                embed.add_field(name="$off", value="turn off autocorrect", inline=False)
                embed.add_field(name="$status", value="shows the status of the bot", inline=False)
                embed.set_footer(text="fuck lennart")
                await message.channel.send(embed=embed)
            
            elif message.content.startswith("$status"):
                embed=discord.Embed(title="GrammarBuddy - Status", description=" ", color=0xd82222)
                embed.add_field(name="Dictionary intake", value=f'{"ON" if self.intake else "OFF"}', inline=True)
                embed.add_field(name="Autocorrect", value=f'{"ON" if self.correcting else "OFF"}', inline=True)
                embed.set_footer(text="fuck jef")
                await message.channel.send(embed=embed)

            else:
                await message.channel.send("command not recognized")

buddy = grammer_buddy()
buddy.run(TOKEN)