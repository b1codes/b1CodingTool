# Skill: /docker init

When the user runs `/docker init`, follow this procedure:

1. **Analyze Project:** Identify if the project is Django, FastAPI, or another Python framework.
2. **Consult User:** Ask which of the following services are needed:
   - PostgreSQL
   - Redis
   - DB Backup Utility
3. **Assemble Files:**
   - Generate a `Dockerfile` using the `dockerfile-python.tmpl` as a base, adjusting the `CMD` and dependency steps as needed.
   - Generate a `compose.yaml` that includes the app service and the requested modular templates from the `templates/` directory.
4. **Environment:** Remind the user to set up a `.env` file with the required variables.
