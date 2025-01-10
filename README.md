# TaskTitan

 TaskTitan is a feature-rich and modern task management application designed to help users organize their goals, habits, routines, and productivity sessions effectively. With a sleek interface, advanced features, and customization options, TaskTitan ensures a seamless experience for planning and managing your time.

 ---

 ## 🚀 Features

 ### **Core Features**
 - **Goal Management**:
   - Add, edit, delete, and organize hierarchical goals.
   - Set priorities, tags, due dates, and attachments.
   - Automatically calculate and display days left for each goal.

 - **Habit Tracking**:
   - Create recurring habits with time and day specifications.
   - Integrated habit progress into the daily planner.

 - **Routine Management**:
   - Schedule routines with start and end dates.
   - Assign specific days of the week for better flexibility.

 - **Daily Planner**:
   - Populate tasks, habits, routines, and goals for each day.
   - Integrated calendar view for efficient planning.

 - **Pomodoro Timer**:
   - Focus timer with customizable work and break intervals.
   - Distraction tracking for improved productivity insights.

 ### **Customization**
 - **Color Themes**:
   - Elegant dark mode with customizable colors.
   - Choose specific colors for calendar elements and UI highlights.

 - **Customizable Goals and Events**:
   - Attach files, assign tags, and organize by priority.
   - Export and import plans in JSON or CSV formats.

 - **Visualization**:
   - Analyze your progress with charts and visual breakdowns.

 ### **Data Management**
 - Backup and restore your data securely.
 - Import/export goals, habits, and events in CSV or JSON formats.

 ---

 ## 📦 Installation

 ### **Using Python and PyInstaller**
 1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/TaskTitan.git
    ```
 2. Navigate to the project directory:
    ```bash
    cd TaskTitan
    ```
 3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
 4. Run the application:
    ```bash
    python TaskTitan.py
    ```

 ### **Build an Executable**
 To package the application into an executable:
 1. Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
 2. Create the executable:
    ```bash
    pyinstaller --onefile --icon=icon.ico TaskTitan.py
    ```
 3. The `.exe` file will be available in the `dist` folder.

 ---

 ## 🖌️ Customization

 ### **Changing Colors**
 You can modify the application's color palette by editing the `colors_config.json` file. Here’s an example configuration:
 ```json
 {
     "calendar_color": "#1E1E2E",
     "past_week_color": "#2A2E45",
     "current_week_color": "#4F46E5",
     "future_week_color": "#264653"
 }
 ```

 ---

 ## 🔧 Requirements

 - Python 3.8 or later
 - PyQt5
 - Matplotlib
 - SQLite3
 - darkdetect

 Install dependencies using:
 ```bash
 pip install -r requirements.txt
 ```

 ---

 ## 📖 Usage

 1. **Setting Up**:
    - Launch the application to start managing your tasks.
    - Use the menu bar to set up preferences like birth date, theme colors, and backup options.

 2. **Creating Goals**:
    - Navigate to the "Goals" tab.
    - Add hierarchical goals and assign due dates, priorities, and tags.

 3. **Tracking Habits**:
    - Define daily habits in the "Habits" tab.
    - Automatically integrates habits into the daily planner.

 4. **Scheduling Routines**:
    - Create routines with specific days and durations.
    - Assign start and end dates for periodic tracking.

 ---

 ## 📊 Visualization

 TaskTitan provides a "Visualization" tab to analyze:
 - Progress of goals and habits.
 - Weekly and monthly performance trends.

 ---

 ## 📁 Backup and Restore

 ### **Backup**:
 1. Go to `File > Backup Data`.
 2. Choose a destination to save the `.db` file.

 ### **Restore**:
 1. Go to `File > Restore Data`.
 2. Select a backup file to restore your data.

 ---

 ## 🛠️ Troubleshooting

 ### Common Issues:
 1. **Missing Dependencies**:
    - Ensure all dependencies are installed:
      ```bash
      pip install -r requirements.txt
      ```

 2. **Application Crashes**:
    - Check the log file (`TaskTitan.log`) for detailed error messages.
    - Ensure that the `planner.db` database is accessible.

 ---

 ## 🤝 Contributing

 We welcome contributions! To contribute:
 1. Fork the repository.
 2. Create a new branch for your feature:
    ```bash
    git checkout -b feature-name
    ```
 3. Commit your changes:
    ```bash
    git commit -m "Added feature"
    ```
 4. Push your branch and create a pull request.

 ---

 ## 📞 Support

 For help or feedback, contact:
 - Email: mahan.dashiti.gohari@gmail.com

"""


**License**
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright 2025 Mahan Dashti Gohari

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.


