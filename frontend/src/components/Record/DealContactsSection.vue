<template>
  <div class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white shadow-sm">
    <div class="flex items-center justify-between gap-2 border-b border-green-100 bg-green-50/60 px-3 py-2">
      <div class="flex items-center gap-2 text-sm font-semibold text-green-900">
        <span class="inline-block size-2 rounded-full bg-green-500" />
        {{ __('Contacts') }}
        <span
          v-if="dealContacts.data?.length"
          class="rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-800"
        >
          {{ dealContacts.data.length }}
        </span>
      </div>
      <Link
        value=""
        doctype="Contact"
        :onCreate="
          (value, close) => {
            _contact = { first_name: value, company_name: organization }
            showContactModal = true
            close()
          }
        "
        @change="(e) => addContact(e)"
      >
        <template #target="{ togglePopover }">
          <Button
            size="sm"
            variant="ghost"
            icon="plus"
            :label="__('Add')"
            @click="togglePopover()"
          />
        </template>
      </Link>
    </div>

    <div
      v-if="dealContacts.loading && !dealContacts.data?.length"
      class="flex items-center justify-center gap-2 px-3 py-4 text-xs text-ink-gray-5"
    >
      <LoadingIndicator class="h-3.5 w-3.5" />
      {{ __('Loading...') }}
    </div>

    <div
      v-else-if="dealContacts.data?.length"
      class="p-2"
      :class="
        dealContacts.data.length > 1
          ? 'grid grid-cols-1 gap-2 sm:grid-cols-2'
          : ''
      "
    >
      <div
        v-for="contact in dealContacts.data"
        :key="contact.name"
        class="flex items-center justify-between gap-2 px-2.5 py-2 hover:bg-surface-gray-1/80"
        :class="
          dealContacts.data.length > 1
            ? 'rounded-md border border-outline-gray-1 bg-surface-white'
            : 'border-b border-outline-gray-1 last:border-b-0'
        "
      >
        <div class="flex min-w-0 items-center gap-2.5">
          <Avatar :label="contact.full_name" :image="contact.image" size="sm" />
          <div class="min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="truncate text-sm font-medium text-ink-gray-9">
                {{ contact.full_name }}
              </span>
              <Badge
                v-if="contact.is_primary"
                variant="outline"
                theme="green"
                :label="__('Primary')"
                class="!px-1.5 !py-0 !text-[10px]"
              />
            </div>
            <div class="flex flex-wrap gap-x-3 text-xs text-ink-gray-5">
              <span v-if="contact.email" class="truncate">{{ contact.email }}</span>
              <span v-if="contact.mobile_no">{{ contact.mobile_no }}</span>
            </div>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-0.5">
          <Button
            size="sm"
            variant="ghost"
            :icon="ArrowUpRightIcon"
            @click="router.push({ name: 'Contact', params: { contactId: contact.name } })"
          />
          <Dropdown :options="contactOptions(contact)">
            <Button size="sm" variant="ghost" icon="more-horizontal" />
          </Dropdown>
        </div>
      </div>
    </div>

    <div v-else class="px-3 py-3 text-xs text-ink-gray-5">
      {{ __('No contacts linked yet') }}
    </div>
  </div>

  <OrganizationModal
    v-if="showOrganizationModal"
    v-model="showOrganizationModal"
    :data="_organization"
    :options="{ redirect: false, afterInsert: (_doc) => emit('organizationCreated', _doc.name) }"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="_contact"
    :options="{ redirect: false, afterInsert: (_doc) => addContact(_doc.name) }"
  />
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import { Avatar, Badge, Button, Dropdown, createResource, toast, call } from 'frappe-ui'
import { h, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  dealId: { type: String, required: true },
  organization: { type: String, default: '' },
})

const emit = defineEmits(['organizationCreated'])

const router = useRouter()
const showContactModal = ref(false)
const showOrganizationModal = ref(false)
const _contact = ref({})
const _organization = ref({})

const dealContacts = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_contacts',
  params: { name: props.dealId },
  cache: ['deal_contacts', props.dealId],
  auto: true,
})

function contactOptions(contact) {
  const options = [
    { label: __('Remove'), icon: 'trash-2', onClick: () => removeContact(contact.name) },
  ]
  if (!contact.is_primary) {
    options.push({
      label: __('Set as Primary'),
      icon: h(SuccessIcon, { class: 'h-4 w-4' }),
      onClick: () => setPrimaryContact(contact.name),
    })
  }
  return options
}

async function addContact(contact) {
  if (dealContacts.data?.find((c) => c.name === contact)) {
    toast.error(__('Contact Already Added'))
    return
  }
  const result = await call('crm.fcrm.doctype.crm_deal.crm_deal.add_contact', {
    deal: props.dealId,
    contact,
  })
  if (result) {
    dealContacts.reload()
    toast.success(__('Contact Added'))
  }
}

async function removeContact(contact) {
  const result = await call('crm.fcrm.doctype.crm_deal.crm_deal.remove_contact', {
    deal: props.dealId,
    contact,
  })
  if (result) {
    dealContacts.reload()
    toast.success(__('Contact Removed'))
  }
}

async function setPrimaryContact(contact) {
  const result = await call('crm.fcrm.doctype.crm_deal.crm_deal.set_primary_contact', {
    deal: props.dealId,
    contact,
  })
  if (result) {
    dealContacts.reload()
    toast.success(__('Primary Contact Set'))
  }
}
</script>
