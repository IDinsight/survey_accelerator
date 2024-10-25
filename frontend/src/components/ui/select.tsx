// src/components/ui/select.tsx

import React from 'react';
import * as RadixSelect from '@radix-ui/react-select';
import { ChevronDownIcon, CheckIcon } from '@radix-ui/react-icons';
import classNames from 'classnames';

interface SelectProps extends RadixSelect.SelectProps {}

const Select = RadixSelect.Root;

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof RadixSelect.SelectTrigger>,
  React.ComponentPropsWithoutRef<typeof RadixSelect.SelectTrigger>
>(({ className, children, ...props }, ref) => (
  <RadixSelect.SelectTrigger
    ref={ref}
    className={classNames(
      'inline-flex items-center justify-between px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
      className
    )}
    {...props}
  >
    {children}
    <RadixSelect.SelectIcon className="ml-2">
      <ChevronDownIcon />
    </RadixSelect.SelectIcon>
  </RadixSelect.SelectTrigger>
));
SelectTrigger.displayName = RadixSelect.SelectTrigger.displayName;

const SelectValue = RadixSelect.SelectValue;

const SelectContent = React.forwardRef<
  React.ElementRef<typeof RadixSelect.SelectContent>,
  React.ComponentPropsWithoutRef<typeof RadixSelect.SelectContent>
>(({ className, children, ...props }, ref) => (
  <RadixSelect.SelectContent
    ref={ref}
    className={classNames(
      'overflow-hidden bg-white rounded-md shadow-lg',
      className
    )}
    {...props}
  >
    <RadixSelect.SelectViewport className="p-2">
      {children}
    </RadixSelect.SelectViewport>
  </RadixSelect.SelectContent>
));
SelectContent.displayName = RadixSelect.SelectContent.displayName;

const SelectItem = React.forwardRef<
  React.ElementRef<typeof RadixSelect.SelectItem>,
  React.ComponentPropsWithoutRef<typeof RadixSelect.SelectItem>
>(({ className, children, ...props }, ref) => (
  <RadixSelect.SelectItem
    ref={ref}
    className={classNames(
      'flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none',
      className
    )}
    {...props}
  >
    <RadixSelect.SelectItemText>{children}</RadixSelect.SelectItemText>
    <RadixSelect.SelectItemIndicator className="ml-auto">
      <CheckIcon className="h-4 w-4 text-blue-500" />
    </RadixSelect.SelectItemIndicator>
  </RadixSelect.SelectItem>
));
SelectItem.displayName = RadixSelect.SelectItem.displayName;

export { Select, SelectTrigger, SelectContent, SelectItem, SelectValue };
