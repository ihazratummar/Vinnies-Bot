# Vinnie's Friend Bot - User Guide

Welcome to **Vinnie's Friend Bot**! This Discord bot allows you to challenge your friends to fun mini-games. This complete point-to-point guide will show you everything you need to know to get started and play.

---

## 🎮 Available Games

Currently, the bot supports two head-to-head games:
1. **Dice**: Roll a 12-sided die. The highest roll wins the round.
2. **Coinflip**: Flip a coin. Heads beats Tails.

---

## 📖 Point-to-Point Guide: How to Play

### 1. Challenging an Opponent
To start a match, you must challenge another user. Keep in mind that games can only be played in designated ticket channels, and you cannot challenge a bot or yourself.

Use one of the following commands in the chat:
- `/dice @username` - Challenges the mentioned user to a game of Dice.
- `/coinflip @username` - Challenges the mentioned user to a game of Coinflip.

### 2. Accepting or Declining a Challenge
Once the command is sent, the bot will display a challenge message with interactive buttons.
- **Accept**: The opponent can click this button to accept the challenge and start the match immediately.
- **Cancel**: Either the opponent or the challenger can click this button to decline or withdraw the challenge.

### 3. Playing a Round
Matches are turn-based. Once a challenge is accepted, the game begins!
- The **Challenger** (the person who initiated the command) always goes first.
- For **Dice**, the bot will ping you and present an action button ("Roll Dice"). Click it to take your turn! Your opponent will then take their turn.
- For **Coinflip**, the bot will present two buttons ("Heads" and "Tails"). The player whose turn it is makes the call! As soon as they click a button, the bot flips one coin and immediately determines the winner.

### 4. Winning a Round
- **Dice**: The player with the higher number wins the round. If there's a tie, players roll again.
- **Coinflip**: If the flipped coin matches the choice you made, you win the round! If it doesn't match, your opponent wins the round.
- The round winner earns **1 point**.
- The winner of the round will get to go first in the next round.

### 5. Winning the Match
The game continues round-by-round until a player reaches the target score.
- The **first player to reach 5 points** wins the entire match!
- Once the match is over, the bot will declare the winner and end the game, freeing both of you up to start a new match.

---

## 🛠️ Admin Commands
The bot owners have access to special commands for testing and moderation.
- `/setdice <1-12>`: Forces the next dice roll in any match to be the exact number specified. 
- `/cancelmatch @user`: Forcefully cancels an active match or pending challenge for the mentioned user. Use this if a game gets stuck or players refuse to play.
*(Note: These commands are restricted to specific Bot Owner IDs and can be used privately in DMs with the bot!)*

---

## ❓ Troubleshooting & Common Errors

- **"You already have an active match / pending challenge"**: You can only be in one match at a time. Finish your current match or click the "Cancel" button on your pending challenge before starting a new one.
- **"You cannot challenge a bot!"**: Make sure you are tagging a real human user.
- **"You must accept the challenge in the same channel it was made"**: Ensure you interact with the bot in the channel where the challenge was originally sent.

Enjoy playing Vinnie's Friend Bot!
