"""
Windows Service wrapper for Agent7 Scheduler.
Allows the scheduler to run as a background service.
"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import traceback


class Agent7SchedulerService(win32serviceutil.ServiceFramework):
    """Windows service for Agent7 scheduler."""
    
    _svc_name_ = "Agent7Scheduler"
    _svc_display_name_ = "Agent7 Task Scheduler"
    _svc_description_ = "Manages scheduled task resumption for Agent7 AI system"
    
    def __init__(self, args):
        """Initialize the service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        
        # Get service directory
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.service_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            self.service_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.db_path = os.path.join(self.service_dir, "agent7.db")
        self.log_file = os.path.join(self.service_dir, "scheduler_service.log")
    
    def log(self, msg):
        """Write to log file."""
        try:
            with open(self.log_file, 'a') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {msg}\n")
        except:
            pass
    
    def SvcStop(self):
        """Stop the service."""
        self.log("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        self.log("Service stopped")
    
    def SvcDoRun(self):
        """Run the service."""
        self.log("Service starting")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self.main()
        except Exception as e:
            self.log(f"Service error: {e}")
            self.log(traceback.format_exc())
    
    def main(self):
        """Main service loop."""
        self.log(f"Initializing scheduler with database: {self.db_path}")
        
        try:
            # Import here to avoid issues with service context
            sys.path.insert(0, self.service_dir)
            from database import Database
            from session_manager import SessionManager
            
            db = Database(self.db_path)
            session_manager = SessionManager(db)
            
            # Set up resume callback
            def resume_callback(checkpoint):
                """Callback when task should resume."""
                self.log(f"Resume callback triggered for task {checkpoint['task_id']}")
                # The actual resumption will be handled by the web server
                # This service just manages the scheduling
            
            session_manager.set_resume_callback(resume_callback)
            
            self.log("Scheduler initialized successfully")
            self.log("Starting scheduler loop...")
            
            # Run scheduler with shorter check interval for service
            check_interval = 30  # Check every 30 seconds
            
            while self.running:
                try:
                    # Check for scheduled tasks
                    from datetime import datetime
                    current_time = datetime.now()
                    scheduled_checkpoints = db.get_scheduled_checkpoints(current_time)
                    
                    for checkpoint in scheduled_checkpoints:
                        task_id = checkpoint['task_id']
                        self.log(f"Task {task_id} ready to resume")
                        
                        # Call resume callback
                        if session_manager.resume_callback:
                            try:
                                session_manager.resume_callback(checkpoint)
                                self.log(f"Task {task_id} resume callback completed")
                            except Exception as e:
                                self.log(f"Error in resume callback for task {task_id}: {e}")
                        
                        # Mark checkpoint as processed
                        db.delete_checkpoint(checkpoint['id'])
                        self.log(f"Checkpoint for task {task_id} processed")
                    
                    # Wait for check interval or stop event
                    result = win32event.WaitForSingleObject(
                        self.stop_event,
                        check_interval * 1000  # milliseconds
                    )
                    
                    if result == win32event.WAIT_OBJECT_0:
                        # Stop event was signaled
                        break
                        
                except Exception as e:
                    self.log(f"Error in scheduler loop: {e}")
                    self.log(traceback.format_exc())
                    time.sleep(check_interval)
            
            self.log("Scheduler loop ended")
            
        except Exception as e:
            self.log(f"Fatal error in service: {e}")
            self.log(traceback.format_exc())


def install_service():
    """Install the Windows service."""
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(Agent7SchedulerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(Agent7SchedulerService)


if __name__ == '__main__':
    """Handle command line or run as service."""
    
    if len(sys.argv) > 1:
        # Handle command line arguments
        cmd = sys.argv[1].lower()
        
        if cmd == 'install':
            print("Installing Agent7 Scheduler Service...")
            try:
                win32serviceutil.InstallService(
                    Agent7SchedulerService._svc_reg_class_,
                    Agent7SchedulerService._svc_name_,
                    Agent7SchedulerService._svc_display_name_,
                    startType=win32service.SERVICE_AUTO_START,
                    description=Agent7SchedulerService._svc_description_
                )
                print("✅ Service installed successfully")
                print("   Use 'net start Agent7Scheduler' to start the service")
            except Exception as e:
                print(f"❌ Installation failed: {e}")
                sys.exit(1)
        
        elif cmd == 'remove' or cmd == 'uninstall':
            print("Removing Agent7 Scheduler Service...")
            try:
                win32serviceutil.RemoveService(Agent7SchedulerService._svc_name_)
                print("✅ Service removed successfully")
            except Exception as e:
                print(f"❌ Removal failed: {e}")
                sys.exit(1)
        
        elif cmd == 'start':
            print("Starting Agent7 Scheduler Service...")
            try:
                win32serviceutil.StartService(Agent7SchedulerService._svc_name_)
                print("✅ Service started successfully")
            except Exception as e:
                print(f"❌ Start failed: {e}")
                sys.exit(1)
        
        elif cmd == 'stop':
            print("Stopping Agent7 Scheduler Service...")
            try:
                win32serviceutil.StopService(Agent7SchedulerService._svc_name_)
                print("✅ Service stopped successfully")
            except Exception as e:
                print(f"❌ Stop failed: {e}")
                sys.exit(1)
        
        elif cmd == 'restart':
            print("Restarting Agent7 Scheduler Service...")
            try:
                win32serviceutil.RestartService(Agent7SchedulerService._svc_name_)
                print("✅ Service restarted successfully")
            except Exception as e:
                print(f"❌ Restart failed: {e}")
                sys.exit(1)
        
        elif cmd == 'status':
            try:
                status = win32serviceutil.QueryServiceStatus(Agent7SchedulerService._svc_name_)
                status_map = {
                    win32service.SERVICE_STOPPED: "Stopped",
                    win32service.SERVICE_START_PENDING: "Starting",
                    win32service.SERVICE_STOP_PENDING: "Stopping",
                    win32service.SERVICE_RUNNING: "Running",
                    win32service.SERVICE_CONTINUE_PENDING: "Continuing",
                    win32service.SERVICE_PAUSE_PENDING: "Pausing",
                    win32service.SERVICE_PAUSED: "Paused"
                }
                print(f"Service Status: {status_map.get(status[1], 'Unknown')}")
            except Exception as e:
                print(f"Service is not installed or error: {e}")
        
        else:
            # Default handler
            win32serviceutil.HandleCommandLine(Agent7SchedulerService)
    else:
        # Running as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(Agent7SchedulerService)
        servicemanager.StartServiceCtrlDispatcher()


