As an AI language model, I don't have the capability to directly access files or directories. However, I can guide you through the process of refactoring operational scripts based on common practices. Since you've mentioned `AGENTS.md` and `TOOLS.md`, I'll provide an example of how you could refactor these files for better clarity and maintainability.

**Original AGENTS.md (Before Refactoring):**

```
AgentID: 001
Name: John Doe
Role: Analyst
Skills: Data Analysis, Statistics, Python
Tools: Excel, R, Python, Tableau

AgentID: 002
Name: Jane Smith
Role: Data Scientist
Skills: Machine Learning, Python, R, SQL, SQL Server
Tools: R, Python, SQL Server, Power BI, Jupyter Notebook
```

**Refactored AGENTS.md (After Refactoring):**

```
Agents:
  - ID: 001
    Name: John Doe
    Role: Analyst
    Skills: Data Analysis, Statistics, Python
    Tools: Excel, R, Python, Tableau

  - ID: 002
    Name: Jane Smith
    Role: Data Scientist
    Skills: Machine Learning, Python, R, SQL, SQL Server
    Tools: R, Python, SQL Server, Power BI, Jupyter Notebook
```

**Original TOOLS.md (Before Refactoring):**

```
ToolID: Excel
Description: Spreadsheet software for data manipulation and analysis.
Usage: Data Entry, Formulas, Charts
AgentID: 001, 002
```

**Refactored TOOLS.md (After Refactoring):**

```
Tools:
  - ID: Excel
    Name: Excel
    Description: Spreadsheet software for data manipulation and analysis.
    Usage: Data Entry, Formulas, Charts
    Applicable Agents: 001, 002

  - ID: R
    Name: R
    Description: Open-source language and environment for statistical computing and graphics.
    Usage: Data Analysis, Statistical Modeling
    Applicable Agents: 001, 002
```

**Refactor Plan:**

1. **Consolidate Agent Information**: Combine the agent information into a single table or structured list with unique identifiers for each agent. This eliminates redundancy and clarifies the roles and skills of each agent.

2. **Standardize Naming Conventions**: Use consistent naming for IDs, such as using "ID:" instead of "AgentID:" to maintain uniformity across documents.

3. **Separate Tools into a Dedicated File**: Move all tool information into a separate file like TOOLS.md. This streamlines the process of managing tools and eliminates the need to search through agent files for tool details.

4. **Create a Reference List**: Maintain a reference list of applicable agents for each tool to avoid repetition and make it easier to track which tools are used by which agents.

**Risk Assessment:**

1. Data Integrity: Ensure that there is no loss of data during the transfer process. All current agent information must be backed up before any changes are made.

2. Access Control: Update any access permissions to reflect the new structure of the files. Agents using old file structures must be reconfigured to access the new format.

3. Dependency Mapping: Identify any scripts or processes that may be dependent on the old file structure and update them accordingly to avoid breaking those components.

4. Testing: Before applying the changes to the live formation node, test the new structure in a controlled environment to ensure there are no unforeseen issues.

5. Documentation: Update any relevant documentation to reflect the new file structure and ensure that all stakeholders are aware of the changes.

**Executing the Changes:**

- Back up the current `AGENTS.md` and `TOOLS.md` files.
- Create new files with the proposed structure.
- Migrate the data from the old files to the new format.
- Update any related scripts or processes to reference the new file structure.
- Test the new structure in a staging environment.
- Once testing is complete and all is confirmed to be working as expected, apply the changes to the live formation node.
- Monitor the new structure closely for any issues that may arise after the change.