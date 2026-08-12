# Automatic Process Assistant User Guide

This guide is for everyday users - no code or technical background needed, just how to use it.

## What this software does

A few clicks and one form, and it automatically handles three things:

1. **Create folders** - automatically creates a project folder on the Engineer, Drafting, and Admin drives, named from the job number and address (the Engineer drive also gets 6 fixed subfolders created automatically).
2. **Fill Word documents** - automatically generates six documents (Project register, PS1, LBP form, Calculation Statement, Specifications, B2 Letter), filled in with the information you entered.
3. **Sync to MinuteDock** - creating a project also automatically creates the matching Contact and Project on MinuteDock.

All three happen together on every Create - a MinuteDock access token must be set up in Settings before you can use the app at all (see below).

## Installing

1. Double-click `AutomaticProcess-Setup.exe`.
2. Windows may show a security warning ("unrecognized publisher" or similar) - click "Run anyway." This is because the installer isn't digitally signed, not a sign of a problem with the software.
3. Click through "Next," choosing whether you want a desktop shortcut.
4. Once installed, you'll find "Automatic Process Assistant" in the Start Menu, and on the desktop if you chose that option.

For a future version, just run the new Setup.exe again to install over the old one - no need to uninstall first.

## First thing to do after opening: Settings

The first time you open the app, there's a **Settings** button in the top-right corner of the window (you can open it any time afterward too).

### The three drive paths (required)

- **Engineer drive**, **Drafting drive**, **Admin drive**: enter the path to each of these three drives on the NAS (or later, a synced OneDrive/SharePoint folder if you switch). Click the **Browse...** button next to each one to pick the folder instead of typing the path by hand.
- All three need to be filled in before clicking **Save** takes effect. You only need to set these once - they'll be remembered for every project after that.

### MinuteDock access token (required)

The app syncs every project to MinuteDock automatically, so this token is required - **Save** won't take effect until it's filled in, alongside the three drive paths above.

**How to get this token:**

1. Open a browser and log in to your MinuteDock account (minutedock.com).
2. Click your avatar/username in the top right and open **Profile**.
3. Find **Manage Access Tokens** and click into it.
4. Click **Create Token**, give it a recognizable name (e.g. "Automatic Process Assistant"), and choose which MinuteDock account it should use.
5. A long string of characters will be shown - **this is only ever shown once**, so copy it immediately. Once you leave the page you won't be able to see it again (if you lose it, you'll just need to create a new one).
6. Back in Automatic Process Assistant's Settings window, paste that string into the **MinuteDock token** field.
7. Click the **Test connection** button next to it - if you see a "connection successful" message with your account name, it's entered correctly.
8. Click **Save**.

The **MinuteDock** step (where you set how this project should be billed on MinuteDock, see below) appears while filling in project details every time - this token is required to move past Settings at all.

Treat this token like a password - don't share it with anyone who doesn't need it. If you think it's been compromised, go back to the Manage Access Tokens page on MinuteDock, delete the old one, and create a new one.

## Filling in a new project

Once Settings is done, you're ready to use the app normally. The top of the window shows "Step X of Y" - just follow it step by step. Click **Next >** at the bottom right to move to the next step once the current one is filled in, or **< Back** to go back and change something.

### General (basic project info)

- **Job number**: the project's job number.
- **Client info**: client details.
- **Street / Suburb / Town**: the address, split into three fields (only the Street field is used to build the project folder name, e.g. "1234 - 211 Ferry Rd").
- After you fill in Job number and Street, a message below will tell you in real time whether that project name is "already in use" - if it shows in red, that name has already been used and you'll need to change the Job number or Street before you can continue.
- **Scope**: tick whichever project types apply (Foundation / Retaining / Beams / Portal / Bracing / Others). For each one you tick, you need to fill in a description in the box next to it (one line per point - press Enter between lines, and each line will become its own bullet point in the generated documents). At least one must be ticked.
- **Role**: your role on this project - Carried out or Supervised. Pick one.

### PS1 Input (information for the PS1 report)

- **Council name**: pick from the dropdown. If the council you need isn't listed, click **Add Council...** to add it (it'll stay in the list from then on); use **Edit Council...** to rename one.
- **Description of work**, **Legal description**, **Site verification**: three multi-line text boxes - fill in as appropriate.
- **Scope of statement**: choose All or Part only.
- **Level of construction monitoring**: CM1 through CM5, multiple selections allowed.
- **Basis of statement**: Compliance and Alternative are two independent checkboxes - you can tick just one, or both, but at least one must be ticked.
  - Ticking Compliance enables the **Compliance method(s)** options below it (B1/VM1, B1/MV4, B1/AS1 - multiple selections allowed).
  - Ticking Alternative enables the **Alternative solution** text box below it, which then becomes required; if left unticked, this field is automatically filled with "N/A" - no need to touch it.
- **Date**: fill in a 4-digit Year first - Month can't be picked until Year is valid, and Day can't be picked until Month is chosen (the day count is automatically correct for the month/leap year). Or just click **Today** to fill in today's date in one click.

### Inspection Schedule

This step corresponds to the "Schedule 3 - Schedule of Inspections" table in the PS1 report.

- Tick whichever of the 7 common inspection items apply.
- If you need additional inspection items, click **Add Other** to add as many as you like - each one needs an **Item of inspection** and a **Time frame** filled in; click the **Remove** button next to one to delete it.
- The list box below shows the current order of everything selected (both fixed items and any Other items you added). Select an item in the list and use **Move Up** / **Move Down** to reorder it - this order becomes the numbering in the final document's table (starting from 1), and fixed items and Other items can be freely mixed in any order, not just Other-items-always-last.
- At least one item must be selected.

### Waivers and Modifications (for the LBP form)

- First choose **Yes** or **No** (whether a waiver or modification of the Building Code is required).
- Only when Yes is chosen do you need to fill in **Building Code Clause** and **Waiver/modification required** below - both become required. Choosing No automatically clears and disables both fields - no need to touch them.

### Specification (selecting sections)

- Tick whichever sections apply (7 options: GENERAL STRUCTURAL CONSTRUCTION / EXCAVATION AND HARDFILL / CONCRETE - GENERAL / REINFORCING STEEL / STRUCTURAL STEELWORK / STRUCTURAL TIMBER / MASONRY BLOCKWORK). At least one must be ticked - any section left unticked is removed entirely from the final document.
- Some sections reveal extra numeric fields once ticked:
  - Excavation: Ultimate bearing capacity (kPa).
  - Concrete: Precast elements / Foundations-Plain Concrete / Foundations-Fibre Concrete / Metal deck topping, all in MPa.
  - Masonry Blockwork: Grout strength - this one is a dropdown (17.5 MPa (Zone B) / 20 MPa (Zone C) / 25 MPa (Zone D)), not typed by hand.
- These fields are only enabled/required while their section is ticked - unticking a section automatically clears and disables its fields.

### B2 Letter (material selection)

- Tick whichever materials apply (Reinforced concrete / Structural timber / Mild steel structure) - at least one must be ticked. Whichever you tick, the matching row stays in the B2 Letter document's compliance table; unticked ones are removed. The row content itself is fixed - this step only decides which rows appear.

### MinuteDock (always appears)

Every project is created as billable on MinuteDock automatically - there's no toggle for this, since unchecking it on MinuteDock's own side stops time entries from being logged against that project at all.

- Choose one billing method:
  - **Use contact rates**: uses whatever default rate is already set for this client in MinuteDock.
  - **Set a standard rate for this project**: sets a fixed hourly rate just for this project - only when this is chosen do you need to fill in the rate below it.

### Review & Create (confirm and generate)

The final step - the button changes to **Create**. Clicking it makes the software, in order:

1. Create the project folders on all three drives.
2. Generate the six Word documents.
3. Sync the matching Contact and Project to MinuteDock.

While this runs, a small "Creating project, please wait..." window with a moving progress bar will appear - this is completely normal and means the software is working in the background, not stuck. It usually takes a few seconds to around ten seconds depending on the number of documents and network conditions; the window being temporarily unresponsive during this time is expected.

Once everything succeeds, a green checkmark "Done" message appears - click OK to close it, and the software automatically clears everything project-specific (your drive settings, MinuteDock token, and council list are all "long-term settings" and are NOT cleared), returning you to the General step, ready to start the next project.

**If something fails partway through** (e.g. a document fails to generate, or the MinuteDock sync fails): a warning will tell you exactly what succeeded and what failed. Anything that already succeeded (folders, documents already generated) is kept, not undone. **In this situation, don't just click Create again right away** - since the folders already exist, clicking again will fail immediately with an "already exists" error. Instead, figure out what went wrong first (e.g. a wrong MinuteDock token - go fix it in Settings), then contact whoever maintains this software if you're not sure how to proceed.

## Frequently Asked Questions

**Q: What does "Already exists on: ..." on the General step mean?**
It means a project folder for this Job number + Street combination has already been created on one of the drives. Change the Job number or Street to continue - this exists to prevent two different projects from overwriting the same folder name.

**Q: Why won't Settings let me past it?**
All three drive paths and the MinuteDock token are required - **Save** won't take effect until every one of them is filled in. Use **Test connection** to confirm the token itself is correct.

**Q: The Council name dropdown is empty and won't open?**
That means no council names have been added yet - click **Add Council...** to add the first one.

**Q: A Word document failed partway through generation?**
The most common cause is that the document being generated is currently open in Word by someone else (e.g. a colleague has the template file open to look at it) - close it in Word and try again.
