
<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Event Management</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="scheduleEvent">
              <v-text-field
                label="Time of Day"
                v-model="timeOfDay"
                type="time"
              />
              <v-btn type="submit" color="primary">Schedule Event</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EventManagement',
  data() {
    return {
      timeOfDay: '08:00',
    };
  },
  methods: {
    scheduleEvent() {
      axios.post('/event/schedule', { time_of_day: this.timeOfDay })
        .then(response => {
          this.$emit('notify', response.data.message);
        });
    },
  },
};
</script>
