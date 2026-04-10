with open("src/blank_business_builder/autonomous_business.py", "r") as f:
    content = f.read()

content = content.replace("""            if task.dependencies:
                deps_complete = all(dep_id in self.completed_task_ids for dep_id in task.dependencies)
                if not deps_complete:
                    task.status = TaskStatus.BLOCKED
                    is_blocked = True

            if is_blocked:
                # Keep in queue for later retry
                remaining_tasks.append(task)
                continue

            # Dependencies met. If it was blocked, it's now unblocked.
            if task.status == TaskStatus.BLOCKED:
                task.status = TaskStatus.PENDING""", """            if task.dependencies:
                deps_complete = all(dep_id in self.completed_task_ids for dep_id in task.dependencies)
                if not deps_complete:
                    self._set_task_status(task, TaskStatus.BLOCKED)
                    is_blocked = True

            if is_blocked:
                # Keep in queue for later retry
                remaining_tasks.append(task)
                continue

            # Dependencies met. If it was blocked, it's now unblocked.
            if task.status == TaskStatus.BLOCKED:
                self._set_task_status(task, TaskStatus.PENDING)""")

content = content.replace("""            if agent:
                task.assigned_to = agent.agent_id
                task.status = TaskStatus.IN_PROGRESS
                # Task assigned, do NOT add back to pending queue
            else:""", """            if agent:
                task.assigned_to = agent.agent_id
                self._set_task_status(task, TaskStatus.IN_PROGRESS)
                # Task assigned, do NOT add back to pending queue
            else:""")

with open("src/blank_business_builder/autonomous_business.py", "w") as f:
    f.write(content)
