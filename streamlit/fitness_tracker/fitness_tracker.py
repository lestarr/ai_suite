import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# Constants
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
EXERCISES_FILE = os.path.join(DATA_DIR, "exercises.json")
WORKOUTS_FILE = os.path.join(DATA_DIR, "workouts.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Update constants to include user-specific paths
def get_user_data_path(username):
    """Get path to user-specific data directory"""
    return os.path.join(DATA_DIR, username)

def get_user_files(username):
    """Get paths to user-specific data files"""
    user_dir = get_user_data_path(username)
    return {
        'exercises': os.path.join(user_dir, "exercises.json"),
        'workouts': os.path.join(user_dir, "workouts.json")
    }

# Update init_data_storage to handle user-specific directories
def init_data_storage():
    """Initialize data storage files in the 'data' directory"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Initialize only users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": []}, f)

def init_user_storage(username):
    """Initialize storage for a specific user"""
    user_dir = get_user_data_path(username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    user_files = get_user_files(username)
    default_data = {
        user_files['exercises']: {"exercises": []},
        user_files['workouts']: {"workouts": []}
    }
    
    for file_path, default_content in default_data.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_content, f)

# Update save_user to initialize user storage
def save_user(name):
    users = load_users()
    # Check if user already exists
    if any(user['name'] == name for user in users):
        return False, "User already exists"
    
    users.append({
        "id": len(users) + 1,
        "name": name,
        "created_at": datetime.now().isoformat()
    })
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": users}, f)
    
    # Initialize storage for new user
    init_user_storage(name)
    return True, f"Added user: {name}"

# Update delete_user to remove user data
def delete_user(name):
    """Delete a user and all their data"""
    users = load_users()
    users = [user for user in users if user['name'] != name]
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": users}, f)
    
    # Remove user's data directory
    user_dir = get_user_data_path(name)
    if os.path.exists(user_dir):
        import shutil
        shutil.rmtree(user_dir)

# Update data loading functions to use user-specific files
def load_exercises(username):
    user_files = get_user_files(username)
    with open(user_files['exercises'], 'r') as f:
        data = json.load(f)
        return data["exercises"]

def load_workouts(username):
    user_files = get_user_files(username)
    with open(user_files['workouts'], 'r') as f:
        data = json.load(f)
        return data["workouts"]

# Update save functions to use user-specific files
def save_exercise(name, muscle_group, username):
    exercises = load_exercises(username)
    normalized_name = normalize_exercise_name(name)
    
    # Check if exercise already exists
    for i, ex in enumerate(exercises):
        if normalize_exercise_name(ex['name']) == normalized_name:
            exercises[i] = {
                "name": normalized_name,
                "muscle_group": muscle_group,
                "created_at": ex['created_at']
            }
            break
    else:
        exercises.append({
            "name": normalized_name,
            "muscle_group": muscle_group,
            "created_at": datetime.now().isoformat()
        })
    
    user_files = get_user_files(username)
    with open(user_files['exercises'], 'w') as f:
        json.dump({"exercises": exercises}, f)

def save_workout(exercise, weight, reps, username):
    workouts = load_workouts(username)
    workouts.append({
        "date": datetime.now().strftime('%Y-%m-%d'),
        "exercise": exercise,
        "weight": weight,
        "reps": reps
    })
    user_files = get_user_files(username)
    with open(user_files['workouts'], 'w') as f:
        json.dump({"workouts": workouts}, f)

def load_users():
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
        return data["users"]

def normalize_exercise_name(name):
    """Normalize exercise name: lowercase and strip extra spaces"""
    return " ".join(name.lower().split())

def import_from_csv(file, username):
    """Import workout data from CSV file for specific user"""
    try:
        df = pd.read_csv(file)
        # close the file
        file.close()
        required_columns = ['date', 'exercise', 'weight', 'reps']
        
        if not all(col in df.columns for col in required_columns):
            return False, "CSV must contain columns: date, exercise, weight, reps"
        
        df['exercise'] = df['exercise'].apply(normalize_exercise_name)
        
        # Add new exercises to user's exercise database
        existing_exercises = load_exercises(username)
        existing_names = {normalize_exercise_name(ex['name']) for ex in existing_exercises}
        
        new_exercises = []
        for exercise_name in df['exercise'].unique():
            exercise_name = exercise_name.strip()
            if exercise_name not in existing_names:
                new_exercises.append({
                    "name": exercise_name,
                    "muscle_group": "Other",
                    "created_at": datetime.now().isoformat()
                })
        
        if new_exercises:
            existing_exercises.extend(new_exercises)
            user_files = get_user_files(username)
            with open(user_files['exercises'], 'w') as f:
                json.dump({"exercises": existing_exercises}, f)
        
        # Import workout data
        workouts = load_workouts(username)
        new_workouts = df.to_dict('records')
        
        for workout in new_workouts:
            date = pd.to_datetime(workout['date']).strftime('%Y-%m-%d')
            workouts.append({
                "date": date,
                "exercise": workout['exercise'],
                "weight": float(workout.get('weight', 0)),
                "reps": int(workout['reps'])
            })
        
        user_files = get_user_files(username)
        with open(user_files['workouts'], 'w') as f:
            json.dump({"workouts": workouts}, f)
        
        message = f"Imported {len(new_workouts)} workouts"
        if new_exercises:
            message += f" and added {len(new_exercises)} new exercises. Please categorize them in the Exercises tab."
        
        return True, message
    except Exception as e:
        return False, f"Error importing data: {str(e)}"

def delete_workout(workout_index):
    """Delete a workout entry by its index"""
    workouts = load_workouts()
    if 0 <= workout_index < len(workouts):
        deleted = workouts.pop(workout_index)
        with open(WORKOUTS_FILE, 'w') as f:
            json.dump({"workouts": workouts}, f)
        return True, f"Deleted: {deleted['exercise']} - {deleted['reps']} reps"
    return False, "Invalid workout index"

def get_last_workout(exercise, username):
    """Get the most recent workout for given exercise and user"""
    workouts = load_workouts(username)
    if not workouts:
        return None
    
    df = pd.DataFrame(workouts)
    # Handle date parsing with mixed formats
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    
    # Filter for exercise
    exercise_df = df[df['exercise'] == exercise].sort_values('date', ascending=False)
    
    if not exercise_df.empty:
        return exercise_df.iloc[0]
    return None

def log_workout():
    st.subheader("Log Workout")
    
    exercises = load_exercises(st.session_state.current_user)
    exercise_names = sorted([ex["name"] for ex in exercises], key=str.lower)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        exercise = st.selectbox(
            "Exercise",
            options=exercise_names if exercise_names else ["Add exercises first"],
            placeholder="Select exercise",
            key="workout_exercise_select"
        )
        
        if exercise and exercise != "Add exercises first":
            last_workout = get_last_workout(exercise, st.session_state.current_user)
        else:
            last_workout = None
    
    with col2:
        weight = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            max_value=500.0,
            step=1.0,
            format="%g",
            value=float(last_workout['weight']) if last_workout is not None else 0.0,
            key="workout_weight_input"
        )
    
    with col3:
        reps = st.number_input(
            "Reps",
            min_value=0,
            max_value=100,
            step=1,
            value=int(last_workout['reps']) if last_workout is not None else 0,
            key="workout_reps_input"
        )
    
    if st.button("Log Set", type="primary", key="log_set_button"):
        if exercise and exercise != "Add exercises first":
            if reps > 0:
                save_workout(exercise, weight, reps, st.session_state.current_user)
                st.success("Set logged successfully!")
            else:
                st.error("Please enter number of reps")
        else:
            st.error("Please select an exercise (or add exercises first)")
    
    # Show recent workouts
    show_recent_workouts()
    
    # Show progress chart only for selected exercise
    if exercise and exercise != "Add exercises first":
        st.write("### Exercise Progress")
        workouts = load_workouts(st.session_state.current_user)
        if workouts:
            df = pd.DataFrame(workouts)
            df['date'] = pd.to_datetime(df['date'], format='mixed')
            
            # Filter data for selected exercise
            exercise_data = df[df['exercise'] == exercise].sort_values('date')
            
            if not exercise_data.empty:
                fig = create_progress_chart(exercise_data, exercise)
                st.plotly_chart(fig)
            else:
                st.info(f"No workout data yet for {exercise}")

def delete_exercise(name, username):
    """Delete an exercise from the database"""
    exercises = load_exercises(username)
    exercises = [ex for ex in exercises if ex['name'] != name]
    user_files = get_user_files(username)
    with open(user_files['exercises'], 'w') as f:
        json.dump({"exercises": exercises}, f)

def manage_exercises():
    st.subheader("Exercise Management")
    
    # Sort muscle groups alphabetically
    MUSCLE_GROUPS = sorted(["Arms", "Back", "Chest", "Core", "Full Body", "Legs", "Shoulders", "Other"])
    
    # Add new exercise
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        # Get existing exercise names
        exercises = load_exercises(st.session_state.current_user)
        # Sort exercise names case-insensitively
        existing_names = sorted([ex["name"] for ex in exercises], key=str.lower)
        
        # Add "Add New" option at the top
        exercise_options = ["Add New"] + existing_names
        selected_exercise = st.selectbox(
            "Exercise Name",
            options=exercise_options,
            key="exercise_select"
        )
        
        # Show text input if "Add New" is selected
        if selected_exercise == "Add New":
            new_exercise = st.text_input("New Exercise Name", key="new_exercise_input")
        else:
            new_exercise = selected_exercise
            
    with col2:
        muscle_group = st.selectbox(
            "Muscle Group", 
            MUSCLE_GROUPS,
            key="muscle_group_select"
        )
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Add/Update Exercise", type="primary", key="add_update_button"):
            if new_exercise and new_exercise != "Add New":
                save_exercise(new_exercise, muscle_group, st.session_state.current_user)
                st.success(f"Added/Updated {new_exercise}")
            else:
                st.error("Please enter exercise name")
    
    with col4:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if selected_exercise != "Add New":
            if st.button("🗑️ Delete", type="secondary", help="Delete selected exercise", key="delete_button"):
                if selected_exercise:
                    delete_exercise(selected_exercise, st.session_state.current_user)
                    st.success(f"Deleted {selected_exercise}")
    
    # Show existing exercises with editable muscle groups
    if exercises:
        st.write("### Exercise Library")
        
        # Convert to DataFrame for display
        df = pd.DataFrame(exercises)
        df = df.rename(columns={
            'name': 'Exercise',
            'muscle_group': 'Muscle Group',
            'created_at': 'Added On'
        })
        df['Added On'] = pd.to_datetime(df['Added On']).dt.strftime('%Y-%m-%d')
        
        # Create editable dataframe
        edited_df = st.data_editor(
            df[['Exercise', 'Muscle Group', 'Added On']].sort_values('Exercise'),
            column_config={
                "Exercise": st.column_config.Column(
                    width="medium",
                    disabled=True
                ),
                "Muscle Group": st.column_config.SelectboxColumn(
                    width="medium",
                    options=MUSCLE_GROUPS,
                    required=True
                ),
                "Added On": st.column_config.Column(
                    width="small",
                    disabled=True
                )
            },
            hide_index=True,
            key="exercise_editor"
        )
        
        # Check for changes and update muscle groups
        if edited_df is not None and not df['Muscle Group'].equals(edited_df['Muscle Group']):
            # Update exercises in storage
            updated_exercises = []
            for _, row in edited_df.iterrows():
                exercise_name = row['Exercise']
                new_muscle_group = row['Muscle Group']
                # Find original exercise and update muscle group
                for ex in exercises:
                    if ex['name'] == exercise_name:
                        updated_exercises.append({
                            'name': ex['name'],
                            'muscle_group': new_muscle_group,
                            'created_at': ex['created_at']
                        })
                        break
            
            # Save updated exercises to user-specific file
            user_files = get_user_files(st.session_state.current_user)
            with open(user_files['exercises'], 'w') as f:
                json.dump({"exercises": updated_exercises}, f)
            
            st.success("Updated muscle groups")

def show_recent_workouts():
    workouts = load_workouts(st.session_state.current_user)
    if workouts:
        df = pd.DataFrame(workouts)
        
        if df.empty:
            st.info(f"No workouts logged yet for {st.session_state.current_user}")
            return
            
        # Handle date parsing with mixed formats
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        
        # Sort dates in descending order and get unique dates
        unique_dates = df['date'].dt.strftime('%d %b').unique()
        unique_dates = sorted(unique_dates, reverse=True)
        
        # Get unique exercises for this user
        exercises = sorted(df['exercise'].unique())
        
        # Create pivot table data
        pivot_data = []
        for exercise in exercises:
            row = {'Exercise': exercise}
            exercise_data = df[df['exercise'] == exercise]
            
            for date in unique_dates:
                date_data = exercise_data[exercise_data['date'].dt.strftime('%d %b') == date]
                if not date_data.empty:
                    # Combine all sets for this date
                    sets = []
                    for _, set_data in date_data.iterrows():
                        sets.append(f"{set_data['weight']}kg × {set_data['reps']}")
                    row[date] = ", ".join(sets)
                else:
                    row[date] = ""
            
            pivot_data.append(row)
        
        # Create display dataframe
        display_df = pd.DataFrame(pivot_data)
        
        st.write(f"### Recent Workouts for {st.session_state.current_user}")
        
        # Show the pivot table
        st.data_editor(
            display_df,
            column_config={
                "Exercise": st.column_config.Column(
                    width="medium",
                ),
                **{date: st.column_config.Column(
                    width="large",
                ) for date in unique_dates}
            },
            hide_index=True,
            disabled=True
        )

def show_analytics():
    st.subheader("Analytics")
    workouts = load_workouts(st.session_state.current_user)
    
    if not workouts:
        st.info("No workout data available yet")
        return
    
    df = pd.DataFrame(workouts)
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    
    # Weekly comparison
    st.write("### Weekly Comparison")
    today = pd.Timestamp.now()
    last_week = df[df['date'] > (today - pd.Timedelta(days=14))]
    if not last_week.empty:
        this_week = last_week[last_week['date'] > (today - pd.Timedelta(days=7))]
        prev_week = last_week[last_week['date'] <= (today - pd.Timedelta(days=7))]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("This Week Workouts", len(this_week))
        with col2:
            st.metric("Last Week Workouts", len(prev_week))
    
    # Combined progress chart for all exercises
    st.write("### Combined Exercise Progress")
    
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Get unique exercises and sort them case-insensitively
    exercises = sorted(df['exercise'].unique(), key=str.lower)
    
    # Add a line for each exercise
    for exercise in exercises:
        exercise_data = df[df['exercise'] == exercise].sort_values('date')
        daily_max = exercise_data.groupby(exercise_data['date'].dt.date)['weight'].max().reset_index()
        
        fig.add_trace(go.Scatter(
            x=daily_max['date'],
            y=daily_max['weight'],
            mode='lines+markers',
            name=exercise,
            line=dict(width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="All Exercises Progress",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_progress_chart(exercise_data, exercise_name):
    """Create a progress chart for an exercise"""
    import plotly.graph_objects as go
    
    # Get max weight per day
    daily_max = exercise_data.groupby(exercise_data['date'].dt.date)['weight'].max().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_max['date'],
        y=daily_max['weight'],
        mode='lines+markers',
        name='Max Weight',
        line=dict(width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"{exercise_name} Progress",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        height=400,
        showlegend=False
    )
    
    return fig

def import_exercises_from_csv(file, username):
    """Import exercises from CSV to the exercise database"""
    try:
        df = pd.read_csv(file)
        
        # Get existing exercises
        existing = load_exercises(username)
        existing_names = {ex['name'].lower() for ex in existing}
        
        # Process new exercises
        new_exercises = []
        for _, row in df.iterrows():
            exercise_name = row['exercise'].strip()
            if exercise_name.lower() not in existing_names:
                new_exercises.append({
                    "name": exercise_name,
                    "muscle_group": "Other",  # Default to "Other" for imported exercises
                    "created_at": datetime.now().isoformat()
                })
        
        if new_exercises:
            existing.extend(new_exercises)
            user_files = get_user_files(username)
            with open(user_files['exercises'], 'w') as f:
                json.dump({"exercises": existing}, f)
            
            return True, f"Added {len(new_exercises)} new exercises. Please categorize them in the Exercises tab."
        return True, "No new exercises to add"
        
    except Exception as e:
        return False, f"Error importing exercises: {str(e)}"

def get_unique_export_filename(base_filename):
    """Generate unique filename by adding counter if file exists"""
    filename = base_filename
    counter = 1
    
    while os.path.exists(os.path.join(APP_DIR, filename)):
        # Split filename into name and extension
        name, ext = os.path.splitext(base_filename)
        filename = f"{name}_{counter}{ext}"
        counter += 1
    
    return filename

def main():
    st.title("Fitness Tracker")
    
    # Initialize data storage
    init_data_storage()
    
    # User selection and data management in sidebar
    with st.sidebar:
        st.subheader("User Management")
        
        # Add new user section
        new_user = st.text_input("Add New User")
        col1, col2 = st.columns([4, 1])
        with col2:
            add_clicked = st.button("Add", type="primary")
        
        # Handle add user action
        if add_clicked:
            if new_user:
                success, message = save_user(new_user)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter a username")
        
        st.divider()  # Add visual separation
        
        # User selection section
        users = load_users()
        if users:
            selected_user = st.selectbox(
                "Select User",
                options=[user["name"] for user in users],
                index=0
            )
            st.session_state.current_user = selected_user
            
            # Delete user button
            if st.button("🗑️ Delete User", type="secondary", help="Delete selected user"):
                delete_user(selected_user)
                st.success(f"Deleted user: {selected_user}")
                st.rerun()
        else:
            st.warning("Please add a user first")
            return
            
        # Data Import/Export section
        st.subheader("Data Management")
        
        tab1, tab2 = st.tabs(["Workouts", "Exercises"])
        
        with tab1:
            # Workout data import/export
            csv_file = st.file_uploader("Import Workouts", type=['csv'])
            if csv_file is not None:
                success, message = import_from_csv(csv_file, st.session_state.current_user)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            
            if st.button("Export Workouts"):
                workouts = load_workouts(st.session_state.current_user)
                if workouts:
                    df = pd.DataFrame(workouts)
                    csv = df.to_csv(index=False)
                    
                    # Create base filename with username and date
                    today = datetime.now().strftime('%Y%m%d')
                    base_filename = f"workouts_{st.session_state.current_user}_{today}.csv"
                    
                    # Get unique filename
                    filename = get_unique_export_filename(base_filename)
                    
                    st.download_button(
                        "Download CSV",
                        csv,
                        filename,
                        "text/csv",
                        key='download-csv'
                    )
                else:
                    st.info("No data to export")
        
        with tab2:
            # Exercise database import
            exercise_file = st.file_uploader("Import Exercises", type=['csv'])
            if exercise_file is not None:
                success, message = import_exercises_from_csv(exercise_file, st.session_state.current_user)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["Log Workout", "Exercises", "Analytics"])
    
    with tab1:
        log_workout()
    with tab2:
        manage_exercises()
    with tab3:
        show_analytics()

if __name__ == "__main__":
    main()

    # streamlit run ai_suite/projects/fitness_app/fitness_tracker.py