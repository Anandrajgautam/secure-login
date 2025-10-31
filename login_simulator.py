"""
Interactive Login Simulator - CLI with Bulk Testing
"""

from ueba_system import UEBASystem
import time
import random


def single_login(system):
    """Single user login flow"""
    users = system.get_users()
    print("\nAvailable Users:")
    for idx, (username, phone) in enumerate(users, 1):
        print(f"  {idx}. {username} ({phone})")
    
    try:
        choice = input("\nSelect user (1-20): ").strip()
        user_idx = int(choice) - 1
        if user_idx < 0 or user_idx >= len(users):
            print("❌ Invalid selection")
            return
        
        username, phone = users[user_idx]
        print(f"\n✅ Selected: {username} ({phone})")
        
    except ValueError:
        print("❌ Invalid input")
        return
    
    # Ask how far they got in the flow
    print("\n" + "-"*80)
    print("How far did the user get in the login flow?")
    print("-"*80)
    print("  1. Started auth request (Step 1 only)")
    print("  2. Requested OTP (Step 1 + 2)")
    print("  3. Completed login (Step 1 + 2 + 3)")
    print("  4. Abandoned after auth (Step 1, then stopped) 🚩")
    print("  5. Abandoned after OTP request (Step 1 + 2, then stopped) 🚩")
    
    try:
        flow_choice = int(input("\nSelect flow (1-5): ").strip())
        if flow_choice not in [1, 2, 3, 4, 5]:
            print("❌ Invalid choice")
            return
    except ValueError:
        print("❌ Invalid input")
        return
    
    # Determine steps and abandonment
    if flow_choice == 1:
        steps = [1]
        abandoned = False
    elif flow_choice == 2:
        steps = [1, 2]
        abandoned = False
    elif flow_choice == 3:
        steps = [1, 2, 3]
        abandoned = False
    elif flow_choice == 4:
        steps = [1]
        abandoned = True
    elif flow_choice == 5:
        steps = [1, 2]
        abandoned = True
    
    # Collect parameters once
    print("\n" + "-"*80)
    print("Enter Parameters (press Enter for smart defaults)")
    print("-"*80)
    
    params = {}
    
    # Device ID with suggestions
    device_id = input("Device ID [DEVICE_DEFAULT / BYPASS_TEST / BOT_DEVICE]: ").strip()
    params['device_id'] = device_id if device_id else 'DEVICE_DEFAULT'
    
    # Network Operator with suggestions
    operator = input("Network Operator [405854=Airtel / 310260=T-Mobile / 405857=Jio]: ").strip()
    params['network_operator'] = operator if operator else '405854'
    
    # Latency with suggestions
    latency = input("Latency (ms) [150=Normal / 30=Bot / 500=VPN]: ").strip()
    try:
        params['latency'] = int(latency) if latency else 150
    except:
        params['latency'] = 150
    
    # Fingerprint
    fingerprint = input("Device Fingerprint [FP_DEFAULT / FP_SPOOFED]: ").strip()
    params['fingerprint'] = fingerprint if fingerprint else 'FP_DEFAULT'
    
    # IP Address with suggestions
    ip = input("IP Address [192.168.1.1 / 10.0.0.1]: ").strip()
    params['ip_address'] = ip if ip else '192.168.1.1'
    
    # User Agent
    ua = input("User Agent [Android/12 / iOS/16]: ").strip()
    params['user_agent'] = ua if ua else 'Android/12'
    
    # Process each step
    print("\n" + "="*80)
    print("PROCESSING LOGIN FLOW...")
    print("="*80)
    
    total_risk = 0
    for step in steps:
        step_name = ["Initial Auth", "OTP Request", "OTP Verify"][step-1]
        success = not abandoned or step < len(steps)
        
        risk_score, breakdown = system.log_attempt(username, step, params, success)
        total_risk = max(total_risk, risk_score)
        
        print(f"\n✅ Step {step} ({step_name}): Risk={risk_score:.1f}")
        time.sleep(0.2)
    
    # Check for abandonment flag
    if abandoned:
        abandonment_risk = system.check_abandonment(username, len(steps))
        print(f"\n🚩 ABANDONMENT DETECTED: Additional risk +{abandonment_risk:.1f}")
        total_risk = min(100, total_risk + abandonment_risk)
    
    # Display final results
    print("\n" + "="*80)
    print(f"🎯 FINAL RISK SCORE: {total_risk:.1f}/100")
    
    if total_risk >= 80:
        print("🔴 RISK LEVEL: CRITICAL - BLOCK")
    elif total_risk >= 60:
        print("🟠 RISK LEVEL: HIGH - CHALLENGE")
    elif total_risk >= 40:
        print("🟡 RISK LEVEL: MEDIUM - MONITOR")
    else:
        print("🟢 RISK LEVEL: LOW - ALLOW")
    
    if abandoned:
        print("\n⚠️  User abandoned flow - possible reconnaissance or bot testing")
    
    print("\n✅ Logged to database")
    print("🔄 Dashboard will update automatically")


def bulk_test(system):
    """Bulk user testing with random parameters"""
    print("\n" + "="*80)
    print("BULK USER TESTING")
    print("="*80)
    
    print("\nTest Scenarios:")
    print("  1. Normal Users (10 users, complete flow, normal params)")
    print("  2. Bot Attack (5 users, rapid attempts, low latency)")
    print("  3. Device Switchers (3 users, multiple devices)")
    print("  4. Abandonment Pattern (5 users, incomplete flows)")
    print("  5. Mixed Scenario (All of the above)")
    
    try:
        scenario = int(input("\nSelect scenario (1-5): ").strip())
        if scenario not in [1, 2, 3, 4, 5]:
            print("❌ Invalid choice")
            return
    except ValueError:
        print("❌ Invalid input")
        return
    
    print("\n" + "="*80)
    print("RUNNING BULK TEST...")
    print("="*80)
    
    users = system.get_users()
    
    if scenario == 1 or scenario == 5:
        # Normal users
        print("\n📊 Testing Normal Users...")
        for i in range(10):
            username = users[i][0]
            params = {
                'device_id': f'DEVICE_{username}',
                'network_operator': '405854',
                'latency': random.randint(120, 180),
                'fingerprint': f'FP_{username}',
                'ip_address': f'192.168.1.{i+1}',
                'user_agent': 'Android/12'
            }
            
            for step in [1, 2, 3]:
                risk_score, _ = system.log_attempt(username, step, params, True)
            
            print(f"   ✅ {username}: Risk={risk_score:.1f}")
            time.sleep(0.1)
    
    if scenario == 2 or scenario == 5:
        # Bot attack
        print("\n🤖 Testing Bot Attack...")
        for i in range(5):
            username = users[i][0]
            params = {
                'device_id': f'BOT_DEVICE_{i}',
                'network_operator': '310260',
                'latency': random.randint(30, 50),
                'fingerprint': 'BOT_FP',
                'ip_address': '10.0.0.1',
                'user_agent': 'Python/3.9'
            }
            
            # Rapid attempts
            for attempt in range(15):
                risk_score, _ = system.log_attempt(username, 1, params, False)
                time.sleep(0.05)
            
            print(f"   🚨 {username}: Risk={risk_score:.1f} (15 rapid attempts)")
    
    if scenario == 3 or scenario == 5:
        # Device switchers
        print("\n📱 Testing Device Switchers...")
        for i in range(3):
            username = users[i+10][0]
            
            for dev in range(6):
                params = {
                    'device_id': f'DEVICE_SWITCH_{dev}',
                    'network_operator': '405854',
                    'latency': random.randint(100, 200),
                    'fingerprint': f'FP_SWITCH_{dev}',
                    'ip_address': f'192.168.2.{dev}',
                    'user_agent': 'Android/12'
                }
                
                risk_score, _ = system.log_attempt(username, 1, params, True)
                time.sleep(0.1)
            
            print(f"   🔄 {username}: Risk={risk_score:.1f} (6 devices)")
    
    if scenario == 4 or scenario == 5:
        # Abandonment pattern
        print("\n🚩 Testing Abandonment Pattern...")
        for i in range(5):
            username = users[i+15][0]
            params = {
                'device_id': f'DEVICE_{username}',
                'network_operator': '405854',
                'latency': random.randint(100, 150),
                'fingerprint': f'FP_{username}',
                'ip_address': f'192.168.3.{i}',
                'user_agent': 'Android/12'
            }
            
            # Start flow but abandon
            steps = random.choice([1, 2])  # Stop at step 1 or 2
            for step in range(1, steps + 1):
                risk_score, _ = system.log_attempt(username, step, params, False)
            
            abandonment_risk = system.check_abandonment(username, steps)
            total_risk = min(100, risk_score + abandonment_risk)
            
            print(f"   ⚠️  {username}: Risk={total_risk:.1f} (abandoned at step {steps})")
            time.sleep(0.1)
    
    print("\n✅ Bulk test complete!")
    print("🔄 Check dashboard for results")


def main():
    system = UEBASystem()
    
    print("="*80)
    print("LOGIN SIMULATOR - UEBA Testing")
    print("="*80)
    
    while True:
        print("\n" + "="*80)
        print("Main Menu:")
        print("  1. Single User Login")
        print("  2. Bulk User Testing")
        print("  0. Exit")
        
        try:
            choice = input("\nSelect option (0-2): ").strip()
            
            if choice == '0':
                print("\n👋 Exiting...")
                break
            elif choice == '1':
                single_login(system)
            elif choice == '2':
                bulk_test(system)
            else:
                print("❌ Invalid choice")
                continue
            
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Ask to continue
        cont = input("\nReturn to main menu? (y/n): ").strip().lower()
        if cont != 'y':
            print("\n👋 Exiting...")
            break


if __name__ == "__main__":
    main()
