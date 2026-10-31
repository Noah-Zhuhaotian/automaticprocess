# Automatic Process Assistant User Guide

This guide is for everyday users - no code or technical background needed, just how to use it.

## What this software does

You fill in one step-by-step form, and the software does the repetitive project setup for you:

1. **Creates the project folders** - one folder on each of the Engineer, Drafting and Admin drives, named "job number - street" (e.g. "23432 - 217 Armagh Street"). The Engineer folder also gets 6 fixed subfolders (01 Architectural ... 06 Consent Document).
2. **Fills in the Word documents** - six documents (Project register, PS1 Producer Statement, LBP form, Calculation Statement, Specifications, B2 Letter) are generated from what you entered.
3. **Sets the project up in MinuteDock** - the client (Contact) and the project are created in MinuteDock, so time can be logged against it.

You choose at the start whether to do all three, only create the folders, or come back later to fill in the documents. You can also save your usual settings as a **template**, and create several jobs at once from a template.

Everything you enter for a project is saved, so you can **open the project again later**, change something, and regenerate its documents.

## Installing

1. Double-click `AutomaticProcess-Setup.exe`.
2. Windows may show a security warning ("unrecognized publisher" or similar) - click "Run anyway." This is because the installer isn't digitally signed, not a sign of a problem with the software.
3. Click through "Next," choosing whether you want a desktop shortcut.
4. Once installed, you'll find "Automatic Process Assistant" in the Start Menu, and on the desktop if you chose that option.

**Updating:** just run the new Setup.exe over the old one - no need to uninstall first. Your settings, council list, saved projects and templates are kept: they're stored in your Windows user folder, not in the program folder, so installing a new version (or even uninstalling) never deletes them.

## First thing to do after opening: Settings

The first time you open the app it asks for its Settings. You can change them any time afterwards with the **Settings** button in the top-right corner.

### The three drive paths (required)

- **Engineer drive**, **Drafting drive**, **Admin drive**: the folder on the NAS (or a synced OneDrive/SharePoint folder) where each drive's project folders live. Use **Browse...** to pick the folder instead of typing it.
- All three must be filled in, and all three must be *different* folders - if two are the same, **Save** refuses with a "Duplicate drive path" error (two drives pointing at the same folder would make every Create fail halfway).

### MinuteDock access token (required)

The app sets up every project in MinuteDock, so it needs an access token.

**How to get the token:**

1. Log in to MinuteDock (minutedock.com) in a browser.
2. Click your avatar/username in the top right and open **Profile**.
3. Open **Manage Access Tokens**.
4. Click **Create Token**, give it a name (e.g. "Automatic Process Assistant"), and choose the MinuteDock account.
5. A long string is shown - **it's only shown once**, so copy it straight away (if you lose it, just create a new one).
6. Paste it into the **MinuteDock token** field in Settings.
7. Click **Test connection** - a "connection successful" message with your account name means it's right.
8. Click **Save**.

Treat the token like a password. If you think it's been leaked, delete it on the Manage Access Tokens page and create a new one.

## Step 1 - Choose what to do (Create mode)

Every project starts on the **Create mode** page. Pick one:

| Option | What it does |
|---|---|
| **Create project folders only** | Makes the folders and the MinuteDock project - no documents. Use this to set a job up now and do the paperwork later. |
| **Open an existing project (fill or regenerate its documents)** | Pick an existing project folder, then fill in (or change) its details and generate its documents. |
| **Create folders and documents together (normal)** | Everything at once - folders, the six documents, and MinuteDock. |
| **Create several jobs from a template** | Create many jobs in one go - you only type each job's number, client and address. See "Creating several jobs at once" below. |

**Start from template** (for "folders only", "normal" and "several jobs"): pick a saved template and every page except General is filled in for you. You can still change anything on any page. Choose "(none)" to start blank. See "Templates" below.

### Opening an existing project

When you choose **Open an existing project**, a list of project folders appears. It shows:
- project folders that don't have documents yet (e.g. ones made with "folders only"), and
- any project that was created with this app before, even if it already has documents.

After you pick one, every page is filled in with what was entered last time - just change what you need. The job number and street can't be changed (they're the folder's name). The top of every page shows which folder you're working on.

**Updating vs. creating:** if the project's documents were already generated before, this is an **update** - the last page is called **Review & Update**, its button says **Update**, and a **Changes** section at the top of the summary lists every value you changed (old value → new value). The changed lines are also shown in orange, marked "(updated)", in the rest of the summary. If you changed nothing it says so. If the project has no documents yet (e.g. it was made with "folders only"), it's a normal **Create**.

When updating, the app **moves the old documents into a `_previous versions` folder** (inside the project folder, with the date and time) before making the new ones - nothing is deleted. If one of the old documents is open in Word, close it first.

In MinuteDock, no new project is made - the job's existing project is used, and its budget is only changed if you changed it.

## Step 2 - General

- **Job number**: the job number. **Job numbers must be unique** - you can't continue if the number is already used by any project folder on any of the three drives (whatever its street), or by any project in MinuteDock (including archived ones). A message under the fields tells you straight away if the number is taken.
- **Client info**: pick the client from the list of your MinuteDock contacts. If it's a new client, click **Add new contact...** and type the name - it's added to MinuteDock when you click Create. (**Refresh** reloads the list from MinuteDock. If MinuteDock can't be reached, you can type the name directly.)
- **Street / Suburb / Town**: the address. Only the Street is used in the folder name.

When you're opening an existing project, the client is fixed to the one its MinuteDock project already belongs to.

## Step 3 - Scope

- Tick each scope item that applies (Foundation / Retaining / Beams / Portal / Bracing / Others) and describe it in the box next to it. Press Enter between points - each line becomes its own bullet point in the documents. At least one must be ticked.
- **Role**: Carried out or Supervised.

## Step 4 - PS1 Input

- **Council name**: pick from the list. **Add Council...** adds a new one (it stays in the list from then on); **Edit Council...** renames one.
- **Description of work**, **Legal description**, **Site verification**: free text.
- **Scope of statement**: All or Part only.
- **Level of construction monitoring**: CM1 to CM5, tick any.
- **Basis of statement**: Compliance and/or Alternative (at least one).
  - Compliance enables the **Compliance method(s)**: B1/VM1, B1/VM2, B1/AS1.
  - Alternative fills the **Alternative solution** automatically with "Repairing and rebuilding houses affected by the Canterbury Earthquake December 2012." - nothing to type. If Alternative isn't ticked it shows "N/A".
- **Date**: type the year first, then pick the month and day - or click **Today**.

## Step 5 - Inspection Schedule

This is the "Schedule of Inspections" table in the PS1 report (columns: No., Item of inspection, Time frame).

- Tick which of the 7 standard inspections apply - each already has its time frame (when the inspection happens) filled in.
- **Add Other** adds your own inspection. Its **Item of inspection** box is a dropdown of Other items you've used before - picking one also fills in its **Time frame**. You can also type a new one; new ones are remembered for next time when you click Create. **Remove** deletes a row.
- The list at the bottom is the final order. Select an item and use **Move Up** / **Move Down** - this order becomes the numbering in the table.

## Step 6 - Waivers and Modifications (LBP form)

- Choose **Yes** or **No**. Only with Yes do you fill in **Building Code Clause** and **Waiver/modification required**.

## Step 7 - Specification

- Tick which sections of the Specification apply; unticked sections are removed from the document.
- Some sections have values to fill in (numbers only):
  - **Excavation and Hardfill**: Ultimate bearing capacity (kPa).
  - **Concrete - General**: each strength has its own tickbox - **Precast elements**, **Foundations - Plain Concrete**, **Foundations - Fibre Concrete**, **Metal deck topping**, **Others** (all MPa). Only the ticked ones are written into the document; tick at least one.
  - **Masonry Blockwork**: Grout strength, chosen from a list.

## Step 8 - B2 Letter

- Tick which materials apply (Reinforced concrete / Structural timber / Mild steel structure). Only the ticked rows appear in the letter's table.

## Step 9 - MinuteDock

- **Rates**: always "Use contact rates" (the client's own rate in MinuteDock).
- **Set a budget** (optional): tick it to give the project a **$ Billable** budget **in total** (one amount for the whole project). Numbers only.
- Every project is created as billable - unchecking billable in MinuteDock would stop time being logged against it.

When you're opening an existing project, this page shows the project's current budget from MinuteDock; it's only updated if you change it.

## Step 10 - Review & Create

This page lists **everything you entered** on every page, so you can check it all before creating. To change something, click **< Back**.

Click **Create** (or **Update**, when you're updating an existing project - see "Opening an existing project"). A "please wait" window with a moving bar appears while it works - that's normal; it usually takes a few seconds. When it's done a green ✔ message appears, and the app goes back to the Create mode page for the next project. Your settings, councils and templates are never cleared.

**If something fails partway** (e.g. a document is open in Word, or MinuteDock can't be reached), a message tells you what was created and what failed. What was already created is kept. Don't just click Create again - the folders now exist, so the job number counts as used. Instead, use **Open an existing project** to finish it.

## Templates

A template stores everything **except** the General page (job number, client, address) and the PS1 date: Scope, Role, PS1 Input, Inspection Schedule, Waivers, Specification, B2 Letter, and the MinuteDock budget.

- **Save a template**: fill in a project as usual, and on the Review & Create page click **Save these settings as a template...** and give it a name. (If the name exists, you're asked before it's replaced.)
- **Use a template**: on the Create mode page, choose it under **Start from template**.
- **Manage templates**: click **Manage templates...** on the Create mode page:
  - **Edit values...** - goes through the template's pages so you can change them; the last page's button is **Save template** (nothing is created). **Cancel editing** on the first page leaves without saving.
  - **Rename...** / **Delete**.

## Creating several jobs at once

1. On the Create mode page choose **Create several jobs from a template** and pick the **Template**.
2. On the **Jobs** page:
   - **Date**: the date written into every job's PS1 report. It starts as today - change the year/month/day if you need another date, or click **Today** to go back to today.
   - Fill in one row per job: Job number, Client, Street, Suburb, Town. **Add job** adds a row; **Remove** deletes one.
   - **Client**: pick an existing MinuteDock client from the dropdown. For a new client, click **Add new client...** and type the name - it then appears in every row's dropdown, and it's created in MinuteDock when you click Create all. (You can also just type a new name straight into the Client box.)
3. Click Next - the app checks the date and every row (missing fields, the same job number twice in the table, or a job number that's already used).
4. Review & Create lists all the jobs (new clients are marked "new, added to MinuteDock on Create"), the date, and the template's settings. Click **Create all**.

Each job is created completely (folders, the six documents with the date you chose, MinuteDock - including any new clients) one after another - the progress window shows which one it's on. If one job fails, the others still go ahead. At the end you get a list:

- **OK** - created.
- **PARTIAL** - folders/documents were created but something else failed (e.g. MinuteDock) - fix it later with **Open an existing project**.
- **FAILED** - not created at all; these jobs stay in the table so you can fix them and click **Create all** again.

## Frequently Asked Questions

**Q: It says the job number is already used.**
A project folder with that job number exists on one of the drives (with any street), or a MinuteDock project already uses it. Job numbers must be unique - use another number, or use **Open an existing project** if you meant to work on that existing job.

**Q: Why won't Settings let me past it?**
All three drive paths and the MinuteDock token are required, and the drive paths must all be different. Use **Test connection** to check the token.

**Q: The Council name list is empty?**
No councils have been added yet - click **Add Council...**.

**Q: A Word document failed while generating?**
Usually the file (or the template) is open in Word - close it and try again.

**Q: Where is my saved data kept?**
In your Windows user folder (`%APPDATA%\AutomaticProcess`): settings, saved projects (`projects`), templates (`templates`) and logs. It's only on this computer, and software updates don't remove it.
