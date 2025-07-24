# AI-audiobooks
This repo aims to create a pipeline to voiceover any book given a book text file



pricing

ElevenLabs API pricing:

$22/month: $0.30 per 1k characters

$99/month: $0.24 per 1k characters

$330/month: $0.18 per 1k characters

OpenAI API:

TTS: $0.015 / 1K characters
for a given book, cost of voice over will cost $13,5. Too much, need local tts.
TTS HD: $0.030 / 1K characters

Local model (chatterbox).
Good quality, long execution, especially without new gpu avaliable.
Ryzen 5 5200, takes 90 sec to generate 4 sec audiofile, but quality is nice, good voiceclonning
Nvidia 4060 8gb creates 16 sec of audio in 13 sec, sourse: https://www.youtube.com/watch?v=trgPAtcVNfQ
My laptop Intel i7-12700H 12th gen: 122 sec for 15 sec voicefile.
Nvidia 4070: 8.7 sec for 16 sec audifile
https://www.videocardbenchmark.net/high_end_gpus.html


My own benchmarks:
5060 Ti, created a file from a given voice, 3.5 minutes file, produced in sligtly more than 5 minutes.
another file 20 pages, file duration: , produced: 
