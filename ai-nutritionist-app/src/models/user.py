import sqlite3 as sql

class User:
    def __init__(self, id, height, weight, sex, age, estimated_time, target_weight):
        self.id = id
        self.height = height
        self.weight = weight
        self.sex = sex
        self.age = age
        self.estimated_time = estimated_time
        self.target_weight = target_weight


    # Load user from the database using user ID
    @classmethod
    def load_user_from_db(cls, user_id):
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            SELECT height, weight, sex, age, estimated_time, target_weight FROM users
            WHERE user_id = ?
            ''', (user_id,)
            )
        user_data = cursor_user_history.fetchone()
        conn_user_history.close()
        
        # Check if user_data is None
        if not user_data:
            print(f"User with ID {user_id} not found in database.")
            return None
        return cls(
            id=user_id,
            height=user_data[0],
            weight=user_data[1],
            sex=user_data[2],
            age=user_data[3],
            estimated_time=user_data[4],
            target_weight=user_data[5]
            )
    

    # Log the user into the user_history database
    def log_user_to_db(self, time):
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            INSERT INTO users (user_id, height, weight, sex, age, estimated_time, target_weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.id, self.height, self.weight, self.sex, self.age, self.estimated_time, self.target_weight)
            )
        cursor_user_history.execute('''
            INSERT INTO weight_log (user_id, weight, log_time)
            VALUES (?, ?, ?)
            ''', (self.id, self.weight, time)
            )
        print(f"User {self.id} logged to database.")
        conn_user_history.commit()   
        conn_user_history.close()


    # Update user attributes        
    def update_weight(self, new_weight, time):
        self.weight = new_weight
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            UPDATE users
            SET weight = ?
            WHERE user_id = ?
            ''', (new_weight, self.id)
            )
        cursor_user_history.execute('''
            INSERT INTO weight_log (user_id, weight, log_time)
            VALUES (?, ?, ?)
            ''', (self.id, new_weight, time)
            )
        print(f"User {self.id} weight updated to {new_weight} at {time}.")
        conn_user_history.commit()   
        conn_user_history.close()


    def update_goal_to_db(self, new_estimated_time, new_target_weight):
        self.estimated_time = new_estimated_time
        self.target_weight = new_target_weight
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            UPDATE users
            SET estimated_time = ?, target_weight = ?
            WHERE id = ?
            ''', (new_estimated_time, new_target_weight, self.id)
            )
        print(f"User {self.id} goal updated: estimated_time={new_estimated_time}, target_weight={new_target_weight}.")
        conn_user_history.commit()   
        conn_user_history.close()


    def update_personal_info_to_db(self, height=None, weight=None, sex=None, age=None):
        if height is not None:
            self.height = height
        if weight is not None:
            self.weight = weight
        if sex is not None:
            self.sex = sex
        if age is not None:
            self.age = age
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            UPDATE users
            SET height = ?, weight = ?, sex = ?, age = ?
            WHERE id = ?
            ''', (self.height, self.weight, self.sex, self.age, self.id)
            )
        print(f"User {self.id} personal info updated.")
        conn_user_history.commit()   
        conn_user_history.close()


    # Get user information
    def get_user_info(self):
        return {
            "height": self.height,
            "weight": self.weight,
            "sex": self.sex,
            "age": self.age,
            "estimated_time": self.estimated_time,
            "target_weight": self.target_weight
        }


    def get_user_id(self):
        return self.id
    

    def get_user_food_preference(self, food_name):
        conn_user_gt = sql.connect('user_pred.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT food_preferences FROM users_preference
            WHERE user_id = ? AND food_names = ?
            ''', (self.id, food_name)
            )
        result = cursor_user_gt.fetchone()
        conn_user_gt.close()
        return result[0] if result else 0.5  # Default preference if not found


    def get_user_food_preference_of_type(self, food_type):
        conn_user_gt = sql.connect('user_pred.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT food_names, food_preferences FROM users_preference
            WHERE user_id = ? AND food_types = ?
            ''', (self.id, food_type)
            )
        preferences = cursor_user_gt.fetchall()
        conn_user_gt.close()
        preference_dict = {item[0]: item[1] for item in preferences}
        return preference_dict


    def get_user_activity_level(self):
        conn_user_gt = sql.connect('user_pred.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT activity_level FROM users_activity_level
            WHERE user_id = ?
            ''', (self.id,)
            )
        result = cursor_user_gt.fetchone()
        conn_user_gt.close()
        return result[0] if result else 'moderately_active'  # Default activity level if not set
    

    def get_user_weight_gain_loss_factor(self):
        conn_user_gt = sql.connect('user_pred.db')
        cursor_user_gt = conn_user_gt.cursor()
        cursor_user_gt.execute('''
            SELECT weight_gain_factor, weight_loss_factor FROM user_weight_gain_loss_factor
            WHERE user_id = ?
            ''', (self.id,)
            )
        result = cursor_user_gt.fetchone()
        conn_user_gt.close()
        return (result[0], result[1]) if result else (1.1, 0.9)  # Default factors if not set


    # delete user from database
    def delete_user_from_db(self):
        conn_user_history = sql.connect('user_history.db')
        cursor_user_history = conn_user_history.cursor()
        cursor_user_history.execute('''
            DELETE FROM users
            WHERE user_id = ?
            ''', (self.id,)
            )
        cursor_user_history.execute('''
            DELETE FROM weight_log
            WHERE user_id = ?
            ''', (self.id,)
            )
        cursor_user_history.execute('''
            DELETE FROM meals_log
            WHERE user_id = ?
            ''', (self.id,)
            )
        print(f"User {self.id} deleted from database.")
        conn_user_history.commit()   
        conn_user_history.close()