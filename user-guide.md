# My Little Wins - User Guide

Welcome to **My Little Wins**, a personal progress and growth-tracking game designed to build healthy habits, practice math skills, and recognize efforts. 

The core philosophy of this app is simple:
> *"I am responsible for doing what I said I would do, and I can feel proud of my progress."*

---

## 🚀 Getting Started

When you launch the app, you are presented with the **Profile Selector Screen**:
* **👧 Go to My Little Wins**: Enters the frictionless Child View. No passwords or emails are required, making it easy for kids to open and use.
* **👩 Parent Profile**: Accesses the settings dashboard. This is protected by a 4-digit PIN (default: `1234`) to keep configuration controls secure.

To switch profiles at any time, simply click the **Switch Profile 🔄** button in the top right corner.

---

## 👧 The Child View (Play & Progress)

The child's experience is split into four playful tabs:

### 1. 🏠 TODAY
This is the core daily checklist. It shows her daily missions (e.g. *Tidy your room*, *Read for 20 minutes*, *Complete Math Mission*).
* **Missions Grid**: Clicking on any mission opens its detail card containing:
  - **What to do** (Title)
  - **Why it matters** (Description)
  - **Status** (e.g., `💤 Not reported`, `⏳ Pending Confirmation`, or `✅ Completed`)
* **I DID IT! 🎉 Button**: When she finishes a task, she taps this button. The app updates the status to `"Pending Confirmation"` and encourages her to show her parent.
* **Math Mission (Interactive Quiz)**:
  - Launches a 10-question math quiz tailored to her skill level.
  - **Supportive Retries**: If she makes a mistake, the mascot *Digit the Robot* 🤖 steps in to make mistakes safe: *"That one was tricky! Want to try again?"*
  - **Effort-Based Achievement Labels**: Rather than standard scoring, the quiz grades her progress based on effort:
    - **🌱 Started**: Attempted once.
    - **💪 Kept Going**: Attempted more than once.
    - **🚀 Improved**: Got a higher score on a retry.
    - **🏆 Mastered**: Achieved a perfect 10/10.
  - She can submit her quiz at any point for parent review.

### 2. 📚 READING LOG
A dedicated reading log page where she can archive the books she reads:
* **Log a Book**: Enter the book's title and author, then click **"Log Book 📖"** to add it to her bookshelf.
* **Auto-completion**: Logging a book automatically triggers completion for today's daily reading checklist mission, updating its status to `"Pending Confirmation"`.
* **📖 MY BOOKSHELF**: A beautiful collection of purple bookshelf cards displaying all the books she has read and the dates they were logged.

### 3. 🏆 MY JOURNEY
Displays long-term progress:
* **Lifetime Stars Collected 🌟**: A golden card accumulating every star she has ever earned. Unlike daily progress, this number never resets!
* **Badge Collection 🏅**: A visual grid of achievement badges:
  - `🌱 First Step`: Completed your first mission.
  - `🔥 On Fire`: Built a 3-day completion streak.
  - `💪 Never Give Up`: Improved your score on a math retry.
  - `🧠 Brain Builder`: Mastered a level 3 or higher math quiz.
  - `❤️ Helpful Hero`: Completed 3 helpful category missions.
  - `🌟 Growing Star`: Earned a total of 15 stars.
  - Locked badges are displayed in gray with a lock symbol `🔒` to encourage continued effort.
* **Journey History**: A timeline log of past days showing what dates she completed tasks, what she accomplished, and how many stars were earned.

### 4. 🎁 MY REWARDS
* Displays **yesterday's earned reward** (e.g. *"Yesterday you earned 30 minutes of play time! ❤️"*).
* Shows a preview of **tomorrow's reward** that the parent is planning (e.g., *"Tomorrow's Reward: 30 minutes of Minecraft"*), serving as a motivating bridge between effort and reward.

---

## 👩 The Parent View (Review & Customization)

The parent dashboard is split into two administrative tabs:

### 1. 📊 TODAY'S STATUS & CONFIRMATIONS
* **Today's Daily Checklist**: Monitor the current status of all missions.
* **Pending Completions**: Review tasks your daughter has marked as done.
  - **Encouragement Praise**: You can type a custom praise message (e.g., *"You did a fantastic job cleaning up the blocks! ❤️"*).
  - **Confirm & Add Star ⭐**: Approving a task increments her daily stars count, saves your praise on her screen, and triggers confetti balloons!
  - **Needs More Work 🔄**: Resets the task status back to `"Not reported"` if she needs to spend a little more time on it.

### 2. ⚙️ CONFIGURATION & SETTINGS
* **Tomorrow's Reward**: Enter a custom reward (e.g., *"30 minutes of iPad time"* or *"Trip to the park"*) that will be displayed in her Rewards tab.
* **Edit Daily Missions**:
  - Delete any current tasks.
  - **Add New Daily Mission**: Type a mission title and reason, select a category (`helpful` chores vs `learning` tasks), and click `Add Mission ➕`.
  - **Auto-Formatting**: If you forget to add emojis, the app automatically starts the title with a heart emoji `❤️` and the description with a lightbulb emoji `💡` to keep the UI beautiful!
* **Adjust Stats**: Overwrite total stars, streak count, change her active math level (Levels 1–5), or change your parent PIN.
* **Force Daily Rollover (New Day) ☀️**: A manual testing button that forces the app operating cycle to advance to the next day. Completed missions will automatically archive into her `"My Journey"` tab, and daily stars will reset back to `0` for a fresh start.
* **Send Parent Digest Email**: Compiles a clean HTML summary of accomplishments, stars, and streaks, and emails it to the configured parent address (requires Resend API key setup).

---

## ⚙️ Core Concepts

### 1. Stars Tracking (Daily vs. Total)
* **Stars Today**: The number of daily missions she has completed and had confirmed by you *today*. This count automatically resets to `0` at the start of each daily operating cycle.
* **Total Stars**: Her lifetime cumulative star count. This count never resets, allowing her to watch her collection grow and feel proud of her long-term accomplishments over time.

### 2. 9:00 AM Local Rollover Cycle
Instead of resetting at midnight (when the child is asleep), the application's operating cycle rolls over at **9:00 AM local time**. 
* If she does tasks in the evening or early morning, they will count for the same operating day.
* Rollovers happen automatically the first time the app is opened after 9:00 AM on a new day.

### 3. Streak Protection (Rest Days)
To avoid discouragement, streaks are protected by a single rest day:
* Completing at least **1 mission** increments the streak by 1 day.
* Completing **0 missions** on day 1 preserves the streak (a rest day).
* If **0 missions** are completed for **2 consecutive days**, the streak resets to 0.
