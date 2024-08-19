
<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Configuration</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="updateConfig">
              <v-text-field
                v-for="(value, key) in configInput"
                :key="key"
                :label="key"
                v-model="configInput[key]"
                full-width
              />
              <v-btn type="submit" color="primary">Update Config</v-btn>
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
  name: 'Configuration',
  data() {
    return {
      config: {},
      configInput: {},
    };
  },
  mounted() {
    axios.get('/config')
      .then(response => {
        this.config = response.data;
        this.configInput = { ...response.data };
      });
  },
  methods: {
    updateConfig() {
      axios.post('/config', this.configInput)
        .then(response => {
          this.$emit('notify', response.data.message);
          this.config = { ...this.configInput };
        });
    },
  },
};
</script>
